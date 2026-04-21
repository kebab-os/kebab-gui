import importlib.util
import json
import os
import types

import pygame

from .metadata import parse_kebabapp_metadata
from .static_renderer import create_static_draw_content


APPS_DIR = "src/applications"
DATA_FILE = "storage/data.json"


def save_pinned_apps(pinned):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump({"pinned_apps": pinned}, f)


def load_pinned_apps():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f).get("pinned_apps", [])
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
