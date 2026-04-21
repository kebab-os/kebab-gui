import pygame


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


def load_assets(width, height):
    assets = {
        "favicon": get_img("src/static/system/favicon.png", (16, 16)),
        "wallpaper": get_img("src/static/user/presets/wallpaper2.png", (width, height), False),
        "cursor_img": get_img("src/static/system/cursor.png", (15, 15)),
        "start_icon": get_img("src/static/system/start.png", (24, 24)),
        "close_icon": get_img("src/static/system/close.png", (20, 20)),
        "fullscreen_icon": get_img("src/static/system/fullscreen.png", (14, 14)),
        "windowed_icon": get_img("src/static/system/windowed.png", (14, 14)),
        "shutdown_icon": get_img("src/static/system/shutdown.png", (16, 16)),
        "logout_icon": get_img("src/static/system/logout.png", (16, 16)),
    }
    return assets
