import importlib.util
import configparser
import base64
import json
import os
import types

import kebab_graphics as pygame

from .metadata import parse_kbml_metadata
from .static_renderer import create_static_draw_content


APPS_DIR = "applications"
APP_CACHE_DIR = os.path.join("temporary", "apps_cache")
LEGACY_DATA_FILE = "storage/data.json"
USER_STORAGE_ROOT = os.path.join("storage", "users")
PACKAGE_HEADER = "KBAPP 1"
PACKAGE_FILE_PREFIX = "---FILE:"
PACKAGE_FILE_SUFFIX = "---"
PACKAGE_END_MARKER = "---ENDFILE---"


def _safe_username(username):
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in str(username or "").strip())
    return safe or "user"


def get_user_storage_dir(username):
    return os.path.join(USER_STORAGE_ROOT, _safe_username(username))


def get_user_files_dir(username):
    return os.path.join(get_user_storage_dir(username), "files")


def _get_user_state_ini(username):
    return os.path.join(get_user_storage_dir(username), "state.ini")


def ensure_user_storage(username):
    os.makedirs(get_user_storage_dir(username), exist_ok=True)
    os.makedirs(get_user_files_dir(username), exist_ok=True)


def _parse_kbapp_stack(package_str):
    lines = package_str.splitlines()
    if not lines or lines[0].strip() != PACKAGE_HEADER:
        return None

    entries = {}
    i = 1
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        if not (line.startswith(PACKAGE_FILE_PREFIX) and line.endswith(PACKAGE_FILE_SUFFIX)):
            i += 1
            continue

        rel_path = line[len(PACKAGE_FILE_PREFIX) : -len(PACKAGE_FILE_SUFFIX)].strip().lstrip("/").replace("\\", "/")
        encoding = "utf-8"
        i += 1

        if i < len(lines) and lines[i].strip().startswith("encoding="):
            encoding = lines[i].strip().split("=", 1)[1].strip().lower() or "utf-8"
            i += 1

        if i < len(lines) and lines[i].strip() == "":
            i += 1

        content_lines = []
        while i < len(lines) and lines[i].strip() != PACKAGE_END_MARKER:
            content_lines.append(lines[i])
            i += 1

        payload = "\n".join(content_lines)
        if encoding == "base64":
            compact_payload = "".join(part.strip() for part in content_lines)
            if compact_payload:
                padding = (-len(compact_payload)) % 4
                compact_payload += "=" * padding
                try:
                    entries[rel_path] = base64.b64decode(compact_payload.encode("ascii"))
                except Exception:
                    entries[rel_path] = b""
            else:
                entries[rel_path] = b""
        else:
            entries[rel_path] = payload

        if i < len(lines) and lines[i].strip() == PACKAGE_END_MARKER:
            i += 1

    return entries


def _write_package_entries(extract_dir, entries):
    for rel_path, payload in entries.items():
        abs_path = os.path.join(extract_dir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        if isinstance(payload, bytes):
            with open(abs_path, "wb") as f:
                f.write(payload)
        else:
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(payload)


def _build_fallback_icon(app_name, size):
    surface = pygame.Surface(size, pygame.SRCALPHA)
    app_key = str(app_name or "app").strip().lower()
    palette = {
        "browser": ((76, 132, 255), (240, 246, 255)),
        "calculator": ((54, 181, 121), (242, 250, 245)),
        "files": ((255, 174, 66), (255, 248, 236)),
        "notebook": ((118, 126, 152), (246, 248, 252)),
    }
    bg, fg = palette.get(app_key, ((110, 130, 160), (245, 248, 252)))
    pygame.draw.rect(surface, bg, surface.get_rect(), border_radius=max(4, min(size) // 5))
    if app_key == "browser":
        pygame.draw.circle(surface, fg, (size[0] // 2, size[1] // 2), max(4, min(size) // 5), 2)
        pygame.draw.line(surface, fg, (size[0] // 2, 4), (size[0] // 2, size[1] - 4), 2)
        pygame.draw.line(surface, fg, (4, size[1] // 2), (size[0] - 4, size[1] // 2), 2)
    elif app_key == "calculator":
        pygame.draw.rect(surface, fg, (5, 5, size[0] - 10, 8), border_radius=2)
        for row in range(3):
            for col in range(3):
                pygame.draw.rect(surface, fg, (7 + col * 5, 17 + row * 4, 3, 3), border_radius=1)
    elif app_key == "files":
        pygame.draw.rect(surface, fg, (5, 8, size[0] - 10, size[1] - 13), 2, border_radius=3)
        pygame.draw.rect(surface, fg, (8, 5, 10, 6), border_radius=2)
    elif app_key == "notebook":
        pygame.draw.rect(surface, fg, (7, 5, 4, size[1] - 10), border_radius=2)
        for y in range(9, size[1] - 6, 5):
            pygame.draw.line(surface, fg, (13, y), (size[0] - 5, y), 1)
    else:
        font = pygame.font.SysFont("Segoe UI", max(10, size[1] // 2), bold=True)
        label = font.render(app_key[:1].upper(), True, fg)
        surface.blit(label, ((size[0] - label.get_width()) // 2, (size[1] - label.get_height()) // 2))
    return surface


def save_pinned_apps(pinned, username="user"):
    ensure_user_storage(username)

    parser = configparser.ConfigParser()
    parser["taskbar"] = {
        "pinned_apps": ",".join(pinned),
    }
    with open(_get_user_state_ini(username), "w", encoding="utf-8") as f:
        parser.write(f)


def load_pinned_apps(username="user"):
    ensure_user_storage(username)

    state_file = _get_user_state_ini(username)
    if os.path.exists(state_file) and os.path.getsize(state_file) > 0:
        parser = configparser.ConfigParser()
        parser.read(state_file, encoding="utf-8")
        raw = parser.get("taskbar", "pinned_apps", fallback="")
        return [item.strip() for item in raw.split(",") if item.strip()]

    if os.path.exists(LEGACY_DATA_FILE):
        try:
            with open(LEGACY_DATA_FILE, "r", encoding="utf-8") as f:
                pinned = json.load(f).get("pinned_apps", [])
            if isinstance(pinned, list):
                pinned = [str(item).strip() for item in pinned if str(item).strip()]
                save_pinned_apps(pinned, username)
                return pinned
        except Exception:
            pass

    return []


def load_apps_registry(get_img):
    os.makedirs(APP_CACHE_DIR, exist_ok=True)
    apps_reg = {}
    for item in os.listdir(APPS_DIR):
        if not item.lower().endswith(".kbapp"):
            continue

        app_name = os.path.splitext(item)[0]
        package_path = os.path.join(APPS_DIR, item)
        extract_dir = os.path.join(APP_CACHE_DIR, app_name)

        try:
            if os.path.exists(extract_dir):
                for root, dirs, files in os.walk(extract_dir, topdown=False):
                    for file_name in files:
                        os.remove(os.path.join(root, file_name))
                    for dir_name in dirs:
                        os.rmdir(os.path.join(root, dir_name))

            with open(package_path, "r", encoding="utf-8") as f:
                package_str = f.read()

            entries = _parse_kbapp_stack(package_str)
            if entries is None:
                continue

            os.makedirs(extract_dir, exist_ok=True)
            _write_package_entries(extract_dir, entries)
        except Exception:
            continue

        manifest_file = os.path.join(extract_dir, "app.kbml")
        py_file = os.path.join(extract_dir, "app.py")

        # Parse optional metadata if present.
        config, init_data, static_markup = {}, {}, None
        if os.path.exists(manifest_file):
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    manifest_str = f.read()
                config, init_data, static_markup = parse_kbml_metadata(manifest_str)
            except Exception:
                config, init_data, static_markup = {}, {}, None

        # Load app module if present; otherwise provide a static renderer or placeholder app so the package still appears.
        mod = None
        load_error = None
        if os.path.exists(py_file):
            try:
                spec = importlib.util.spec_from_file_location("app", py_file)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
            except Exception as e:
                load_error = str(e)

        if mod is None or not hasattr(mod, "draw_content"):
            if os.path.exists(manifest_file):
                try:
                    if not static_markup:
                        raise ValueError("Missing content in app.kbml")

                    static_draw = create_static_draw_content(static_markup, extract_dir)

                    if mod is None:
                        mod = types.SimpleNamespace()

                    mod.draw_content = static_draw
                    if not hasattr(mod, "init_data"):
                        mod.init_data = lambda: {}
                except Exception as e:
                    msg = f"Static markup failed: {e}"

                    def _init_data(msg=msg):
                        return {"message": msg}

                    def _fallback_draw_content(surface, rect, data, is_active):
                        inner = pygame.Rect(rect.x + 5, rect.y + 40, rect.w - 10, rect.h - 45)
                        pygame.draw.rect(surface, (250, 250, 252), inner)
                        f_title = pygame.font.SysFont("Segoe UI", 18, bold=True)
                        f_text = pygame.font.SysFont("Segoe UI", 14)
                        surface.blit(f_title.render("App Not Ready", True, (48, 58, 72)), (inner.x + 12, inner.y + 12))
                        surface.blit(f_text.render(msg, True, (100, 110, 124)), (inner.x + 12, inner.y + 42))

                    mod = types.SimpleNamespace(
                        init_data=_init_data,
                        draw_content=_fallback_draw_content,
                    )
            else:
                msg = "Missing app.py and app.kbml"

                def _init_data(msg=msg):
                    return {"message": msg}

                def _fallback_draw_content(surface, rect, data, is_active):
                    inner = pygame.Rect(rect.x + 5, rect.y + 40, rect.w - 10, rect.h - 45)
                    pygame.draw.rect(surface, (250, 250, 252), inner)
                    f_title = pygame.font.SysFont("Segoe UI", 18, bold=True)
                    f_text = pygame.font.SysFont("Segoe UI", 14)
                    surface.blit(f_title.render("App Not Ready", True, (48, 58, 72)), (inner.x + 12, inner.y + 12))
                    surface.blit(f_text.render(msg, True, (100, 110, 124)), (inner.x + 12, inner.y + 42))

                mod = types.SimpleNamespace(
                    init_data=_init_data,
                    draw_content=_fallback_draw_content,
                )

        mod.config = config if config else getattr(mod, "config", {"width": 420, "height": 280})
        mod.init_data_dict = init_data if init_data else getattr(mod, "init_data_dict", {})

        icon_candidates = [
            os.path.join(APPS_DIR, f"{app_name.lower()}.png"),
            os.path.join(APPS_DIR, "notepad.png" if app_name.lower() == "notebook" else f"{app_name}.png"),
            os.path.join(extract_dir, "favicon.png"),
            "favicon.png",
        ]
        icon_path = next((candidate for candidate in icon_candidates if os.path.exists(candidate)), None)
        icon = get_img(icon_path, (22, 22)) if icon_path else None
        if icon is None:
            icon = _build_fallback_icon(app_name, (22, 22))

        apps_reg[app_name] = {
            "module": mod,
            "icon": icon,
        }
    return apps_reg
