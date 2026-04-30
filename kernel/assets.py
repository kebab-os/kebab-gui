import configparser
import json
import os

from graphics import graphics as pygame


SETTINGS_INI_FILE = ".config/settings.ini"
SETTINGS_JSON_LEGACY_FILE = ".config/settings.json"


def _default_settings():
    return {
        "appearance": {"mode": "light"},
        "wallpaper": {"source": "static/user/presets/wallpaper2.png"},
        "vm": {
            "enabled": "false",
            "auto_login": "true",
            "auto_login_user": "admin",
        },
    }


def get_img(path, size, alpha=True):
    try:
        img = pygame.image.load(path)
        if alpha:
            img = img.convert_alpha()
        else:
            img = img.convert()
        return pygame.transform.smoothscale(img, size)
    except Exception:
        return None


def _write_settings_ini(settings):
    parser = configparser.ConfigParser()
    parser["appearance"] = {
        "mode": settings["appearance"]["mode"],
    }
    parser["wallpaper"] = {
        "source": settings["wallpaper"]["source"],
    }
    parser["vm"] = {
        "enabled": settings["vm"]["enabled"],
        "auto_login": settings["vm"]["auto_login"],
        "auto_login_user": settings["vm"]["auto_login_user"],
    }

    os.makedirs(os.path.dirname(SETTINGS_INI_FILE), exist_ok=True)
    with open(SETTINGS_INI_FILE, "w", encoding="utf-8") as f:
        parser.write(f)


def _normalize_settings(raw):
    settings = _default_settings()
    if not isinstance(raw, dict):
        return settings

    appearance = raw.get("appearance", {})
    wallpaper = raw.get("wallpaper", {})
    vm = raw.get("vm", {})

    if isinstance(appearance, dict):
        mode = str(appearance.get("mode", settings["appearance"]["mode"])).strip().lower()
        settings["appearance"]["mode"] = mode if mode in ("light", "dark") else "light"

    if isinstance(wallpaper, dict):
        source = wallpaper.get("source", settings["wallpaper"]["source"])
        if isinstance(source, str) and source.strip():
            settings["wallpaper"]["source"] = source.strip()

    if isinstance(vm, dict):
        for key in ("enabled", "auto_login", "auto_login_user"):
            val = vm.get(key, settings["vm"][key])
            settings["vm"][key] = str(val).strip() if val is not None else settings["vm"][key]

    return settings


def _load_settings_from_ini():
    parser = configparser.ConfigParser()
    parser.read(SETTINGS_INI_FILE, encoding="utf-8")

    settings = _default_settings()
    mode = parser.get("appearance", "mode", fallback=settings["appearance"]["mode"]).strip().lower()
    settings["appearance"]["mode"] = mode if mode in ("light", "dark") else "light"

    source = parser.get("wallpaper", "source", fallback=settings["wallpaper"]["source"]).strip()
    if source:
        settings["wallpaper"]["source"] = source

    settings["vm"]["enabled"] = parser.get("vm", "enabled", fallback=settings["vm"]["enabled"]).strip().lower()
    settings["vm"]["auto_login"] = parser.get("vm", "auto_login", fallback=settings["vm"]["auto_login"]).strip().lower()
    settings["vm"]["auto_login_user"] = parser.get("vm", "auto_login_user", fallback=settings["vm"]["auto_login_user"]).strip()

    return settings


def _load_settings_from_json_legacy():
    try:
        with open(SETTINGS_JSON_LEGACY_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return _default_settings()
    return _normalize_settings(raw)


def load_settings():
    settings = _default_settings()
    if os.path.exists(SETTINGS_INI_FILE) and os.path.getsize(SETTINGS_INI_FILE) > 0:
        settings = _load_settings_from_ini()
    elif os.path.exists(SETTINGS_JSON_LEGACY_FILE) and os.path.getsize(SETTINGS_JSON_LEGACY_FILE) > 0:
        settings = _load_settings_from_json_legacy()

    _write_settings_ini(settings)
    return settings


def load_assets(width, height):
    settings = load_settings()
    wallpaper_source = settings["wallpaper"]["source"]

    assets = {
        "favicon": get_img("static/system/favicon.png", (16, 16)),
        "wallpaper": get_img(wallpaper_source, (width, height), False),
        "cursor_img": get_img("static/system/cursor.png", (15, 15)),
        "start_icon": get_img("static/system/start.png", (24, 24)),
        "close_icon": get_img("static/system/close.png", (20, 20)),
        "fullscreen_icon": get_img("static/system/fullscreen.png", (14, 14)),
        "windowed_icon": get_img("static/system/windowed.png", (14, 14)),
        "shutdown_icon": get_img("static/system/shutdown.png", (16, 16)),
        "logout_icon": get_img("static/system/logout.png", (16, 16)),
        "theme_mode": settings["appearance"]["mode"],
    }
    return assets
