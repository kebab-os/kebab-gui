import importlib.util
import configparser
import json
import os
import types

import kebab_graphics as pygame

from .metadata import parse_kebabapp_metadata
from .static_renderer import create_static_draw_content


APPS_DIR = "applications"
LEGACY_DATA_FILE = "storage/data.json"
USER_STORAGE_ROOT = os.path.join("storage", "users")


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
    apps_reg = {}
    for folder in os.listdir(APPS_DIR):
        p = f"{APPS_DIR}/{folder}"
        kebabapp_file = f"{p}/app.kebabapp"
        py_file = f"{p}/app.py"
        if not os.path.isdir(p):
            continue

        # Parse optional metadata if present.
        config, init_data = {}, {}
        if os.path.exists(kebabapp_file):
            try:
                with open(kebabapp_file, "r") as f:
                    markup_str = f.read()
                config, init_data = parse_kebabapp_metadata(markup_str)
            except Exception:
                config, init_data = {}, {}

        # Load app module if present; otherwise provide a static renderer or placeholder app so folder still appears.
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
            if os.path.exists(kebabapp_file):
                try:
                    with open(kebabapp_file, "r") as f:
                        markup_str = f.read()
                    static_draw = create_static_draw_content(markup_str, p)

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
                msg = "Missing app.py and app.kebabapp"

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

        apps_reg[folder] = {
            "module": mod,
            "icon": get_img(f"{p}/favicon.png", (22, 22)),
        }
    return apps_reg
