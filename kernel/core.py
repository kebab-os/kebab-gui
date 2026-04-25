import kebab_graphics as pygame
import sys
import os

from .app_registry import ensure_user_storage, get_user_files_dir, load_apps_registry, load_pinned_apps, save_pinned_apps
from .assets import get_img, load_assets, load_settings
from .event_handlers import (
    handle_context_menu_click,
    handle_global_shortcuts,
    handle_mouse_motion_with_restore,
    handle_shell_mouse_down,
    handle_start_keyboard,
    handle_window_mouse_down,
    route_keyboard_to_active_app,
    route_mouse_to_active_app,
)
from .login import load_users, run_login_screen
from .renderers import draw_clock, draw_start_menu, draw_taskbar, draw_windows


def _set_dpi_awareness():
    import ctypes

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def _is_truthy(value):
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _resolve_auto_login_user(auto_login_user):
    users = load_users()
    if not users:
        return None

    target = str(auto_login_user or "").strip().lower()
    if target:
        for user in users:
            if str(user.get("username", "")).strip().lower() == target:
                return user

    return users[0]


def boot(vm_mode=False):
    _set_dpi_awareness()

    pygame.init()

    settings = load_settings()
    vm_settings = settings.get("vm", {})
    vm_enabled = vm_mode or _is_truthy(os.environ.get("KEBAB_VM_MODE", "")) or _is_truthy(vm_settings.get("enabled", "false"))
    auto_login_enabled = vm_enabled and _is_truthy(vm_settings.get("auto_login", "true"))
    auto_login_user = vm_settings.get("auto_login_user", "admin")

    info = pygame.display.Info()
    width, height = info.current_w, info.current_h

    display_flags = pygame.FULLSCREEN | pygame.DOUBLEBUF
    if not vm_enabled:
        display_flags |= pygame.HWSURFACE
    if hasattr(pygame, "SCALED"):
        display_flags |= pygame.SCALED

    screen = pygame.display.set_mode((width, height), display_flags)

    try:
        pygame.scrap.init()
    except Exception:
        print("Clipboard support not available")

    pygame.display.set_caption("kebabOS v3.0")

    pygame.mouse.set_visible(False)
    assets = load_assets(width, height)
    if assets["favicon"]:
        pygame.display.set_icon(assets["favicon"])

    if auto_login_enabled:
        current_user = _resolve_auto_login_user(auto_login_user)
    else:
        # Block desktop boot until a valid user signs in.
        current_user = run_login_screen(
            screen,
            width,
            height,
            wallpaper=assets["wallpaper"],
            cursor_img=assets["cursor_img"],
        )
    if current_user:
        pygame.display.set_caption(f"kebabOS v3.0 - {current_user.get('display_name', current_user.get('username', 'User'))}")

    while True:
        username = (current_user or {}).get("username", "user")
        ensure_user_storage(username)
        os.environ["KEBAB_USERNAME"] = username
        os.environ["KEBAB_USER_FILES_DIR"] = get_user_files_dir(username)

        apps_reg = load_apps_registry(get_img)
        open_wins = []
        pinned_apps = load_pinned_apps(username)

        font = pygame.font.SysFont("Segoe UI", 16)
        clock = pygame.time.Clock()
        start_open = False
        active_menu = None
        start_search = ""

        logged_out = False
        while not logged_out:
            if assets["wallpaper"]:
                screen.blit(assets["wallpaper"], (0, 0))
            else:
                screen.fill((240, 240, 240))

            mx, my = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # Handle global shortcuts (Ctrl+Alt+..., Alt+Tab, etc.)
                consumed, open_wins, logout_request = handle_global_shortcuts(event, open_wins, apps_reg, start_open)
                if logout_request:
                    logged_out = True
                    break
                if consumed:
                    continue

                consumed, start_open, start_search, active_menu = handle_start_keyboard(
                    event, start_open, start_search, apps_reg, open_wins, active_menu
                )
                if consumed:
                    continue

                route_keyboard_to_active_app(event, open_wins, start_open)

                handled, active_menu, pinned_apps = handle_context_menu_click(
                    event,
                    mx,
                    my,
                    active_menu,
                    apps_reg,
                    open_wins,
                    pinned_apps,
                    lambda apps: save_pinned_apps(apps, username),
                )
                if handled:
                    continue

                clicked_ui = handle_window_mouse_down(event, mx, my, open_wins, apps_reg, width, height)
                if not clicked_ui:
                    start_open, start_search, active_menu, logout_now = handle_shell_mouse_down(
                        event,
                        mx,
                        my,
                        width,
                        height,
                        start_open,
                        start_search,
                        apps_reg,
                        pinned_apps,
                        open_wins,
                        active_menu,
                    )
                    if logout_now:
                        logged_out = True
                        break

                handle_mouse_motion_with_restore(event, mx, my, open_wins, width, height)
                route_mouse_to_active_app(event, mx, my, open_wins, start_open)

            if logged_out:
                break

            draw_windows(
                screen,
                open_wins,
                mx,
                my,
                assets["close_icon"],
                assets["fullscreen_icon"],
                assets["windowed_icon"],
            )
            draw_taskbar(screen, width, height, mx, my, open_wins, pinned_apps, apps_reg, assets["start_icon"])
            draw_start_menu(
                screen,
                font,
                height,
                mx,
                my,
                start_open,
                start_search,
                apps_reg,
                assets["shutdown_icon"],
                assets["logout_icon"],
            )
            draw_clock(screen, font, width, height)

            if active_menu:
                active_menu.draw(screen, mx, my)
            if assets["cursor_img"]:
                screen.blit(assets["cursor_img"], (mx, my))

            pygame.display.flip()
            clock.tick(60)

        if auto_login_enabled:
            current_user = _resolve_auto_login_user(auto_login_user)
        else:
            current_user = run_login_screen(
                screen,
                width,
                height,
                wallpaper=assets["wallpaper"],
                cursor_img=assets["cursor_img"],
            )
        if current_user:
            pygame.display.set_caption(f"kebabOS v3.0 - {current_user.get('display_name', current_user.get('username', 'User'))}")
