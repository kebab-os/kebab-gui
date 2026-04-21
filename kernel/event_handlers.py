import pygame

from .classes import AppWindow, ContextMenu


TASKBAR_H = 50


def handle_start_keyboard(event, start_open, start_search, apps_reg, open_wins, active_menu):
    if event.type != pygame.KEYDOWN:
        return False, start_open, start_search, active_menu

    mods = pygame.key.get_mods()
    if event.key == pygame.K_x and (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_SHIFT):
        pygame.quit()
        raise SystemExit

    if event.key in (pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_LALT, pygame.K_RALT) and (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_ALT):
        start_open = not start_open
        if start_open:
            start_search = ""
        active_menu = None
        return True, start_open, start_search, active_menu

    if start_open:
        if event.key == pygame.K_ESCAPE:
            return True, False, "", active_menu
        if event.key == pygame.K_BACKSPACE:
            return True, start_open, start_search[:-1], active_menu
        if event.key == pygame.K_RETURN:
            search_results = [n for n in apps_reg.keys() if start_search.lower() in n.lower()]
            if len(search_results) == 1:
                n = search_results[0]
                open_wins.append(AppWindow(n, apps_reg[n]["module"], apps_reg[n]["icon"]))
                return True, False, "", active_menu
            return True, start_open, start_search, active_menu
        if event.unicode and event.unicode.isprintable():
            return True, start_open, start_search + event.unicode, active_menu

    return False, start_open, start_search, active_menu


def route_keyboard_to_active_app(event, open_wins, start_open):
    if event.type == pygame.KEYDOWN and open_wins and not start_open:
        active_win = open_wins[-1]
        if hasattr(active_win.module, "handle_input"):
            try:
                active_win.module.handle_input(event, active_win.app_data, active_win.rect)
            except TypeError:
                active_win.module.handle_input(event, active_win.app_data)


def handle_context_menu_click(event, mx, my, active_menu, apps_reg, open_wins, pinned_apps, save_pinned_apps):
    if not active_menu or event.type != pygame.MOUSEBUTTONDOWN:
        return False, active_menu, pinned_apps

    choice = active_menu.get_choice(mx, my)
    target = active_menu.target
    if choice == "Open":
        open_wins.append(AppWindow(target, apps_reg[target]["module"], apps_reg[target]["icon"]))
    elif choice == "Pin to Taskbar" and target not in pinned_apps:
        pinned_apps.append(target)
        save_pinned_apps(pinned_apps)
    elif choice == "Unpin" and target in pinned_apps:
        pinned_apps.remove(target)
        save_pinned_apps(pinned_apps)

    return True, None, pinned_apps


def handle_window_mouse_down(event, mx, my, open_wins, apps_reg, width, height):
    clicked_ui = False
    for win in reversed(open_wins):
        if event.type == pygame.MOUSEBUTTONDOWN and win.rect.collidepoint(event.pos):
            clicked_ui = True
            if win.close_r.collidepoint(event.pos):
                open_wins.remove(win)
            elif hasattr(win, "fullscreen_r") and win.fullscreen_r.collidepoint(event.pos):
                win.toggle_fullscreen(width, height, taskbar_h=TASKBAR_H)
            elif pygame.Rect(win.rect.right - 15, win.rect.bottom - 15, 15, 15).collidepoint(event.pos):
                win.resizing = True
            else:
                open_wins.remove(win)
                open_wins.append(win)
                if pygame.Rect(win.rect.x, win.rect.y, win.rect.w, 36).collidepoint(event.pos):
                    win.dragging = True
                    win.offset_x, win.offset_y = win.rect.x - mx, win.rect.y - my
                    if getattr(win, "is_fullscreen", False):
                        win.drag_restore_pending = True
                        win.drag_start_x, win.drag_start_y = mx, my
                    else:
                        win.drag_restore_pending = False
            break
    return clicked_ui


def handle_shell_mouse_down(event, mx, my, width, height, start_open, start_search, apps_reg, pinned_apps, open_wins, active_menu):
    if event.type != pygame.MOUSEBUTTONDOWN:
        return start_open, start_search, active_menu, False

    if 8 <= mx <= 44 and height - 42 <= my <= height - 6:
        return (not start_open), start_search, active_menu, False

    if height - TASKBAR_H <= my <= height:
        for i, name in enumerate(pinned_apps):
            if (55 + i * 50) <= mx <= (95 + i * 50):
                if event.button == 1:
                    open_wins.append(AppWindow(name, apps_reg[name]["module"], apps_reg[name]["icon"]))
                elif event.button == 3:
                    active_menu = ContextMenu(mx, my, ["Unpin"], name)
        return start_open, start_search, active_menu, False

    if start_open:
        results = [n for n in apps_reg.keys() if start_search.lower() in n.lower()]
        items = results
        mh = len(items) * 44 + 110
        my_s = height - 60 - mh
        list_top = my_s + 50

        # Bottom icon-only action buttons: logout + shutdown.
        logout_r = pygame.Rect(8 + 118, my_s + mh - 48, 40, 34)
        shutdown_r = pygame.Rect(8 + 162, my_s + mh - 48, 40, 34)
        if logout_r.collidepoint((mx, my)) and event.button == 1:
            return False, "", active_menu, True
        if shutdown_r.collidepoint((mx, my)) and event.button == 1:
            pygame.quit()
            raise SystemExit

        if 8 <= mx <= 218 and list_top <= my <= (list_top + len(items) * 44):
            idx = int((my - list_top) // 44)
            if 0 <= idx < len(results):
                n = items[idx]
                if event.button == 1:
                    open_wins.append(AppWindow(n, apps_reg[n]["module"], apps_reg[n]["icon"]))
                    start_open = False
                elif event.button == 3:
                    active_menu = ContextMenu(mx, my, ["Open", "Pin to Taskbar"], n)
        else:
            start_open = False

    return start_open, start_search, active_menu, False


def handle_mouse_motion_with_restore(event, mx, my, open_wins, width, height):
    if event.type == pygame.MOUSEBUTTONUP:
        for w in open_wins:
            w.dragging = w.resizing = False
            w.drag_restore_pending = False

    if event.type == pygame.MOUSEMOTION:
        for w in open_wins:
            if w.dragging:
                if getattr(w, "is_fullscreen", False) and getattr(w, "drag_restore_pending", False):
                    moved = abs(mx - w.drag_start_x) >= 6 or abs(my - w.drag_start_y) >= 6
                    if moved:
                        grab_ratio_x = (w.drag_start_x - w.rect.x) / max(1, w.rect.w)
                        w.toggle_fullscreen(width, height, taskbar_h=TASKBAR_H)
                        w.rect.x = int(mx - (grab_ratio_x * w.rect.w))
                        w.rect.y = int(my - 16)
                        w.rect.x = max(0, min(w.rect.x, width - w.rect.w))
                        w.rect.y = max(0, min(w.rect.y, (height - TASKBAR_H) - w.rect.h))
                        w.offset_x, w.offset_y = w.rect.x - mx, w.rect.y - my
                        w.drag_restore_pending = False
                    else:
                        continue

                w.rect.x, w.rect.y = mx + w.offset_x, my + w.offset_y

            if w.resizing:
                max_h = max(120, (height - TASKBAR_H) - w.rect.y)
                w.rect.w = max(300, mx - w.rect.x)
                w.rect.h = min(max(200, my - w.rect.y), max_h)


def route_mouse_to_active_app(event, mx, my, open_wins, start_open):
    if not (open_wins and not start_open and event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION, pygame.MOUSEWHEEL)):
        return

    active_win = open_wins[-1]
    if not hasattr(active_win.module, "handle_input"):
        return

    send_event = False
    if event.type == pygame.MOUSEBUTTONDOWN:
        if hasattr(active_win, "content_rect") and active_win.content_rect.collidepoint((mx, my)):
            send_event = True
    elif event.type == pygame.MOUSEWHEEL:
        if hasattr(active_win, "content_rect") and active_win.content_rect.collidepoint((mx, my)):
            send_event = True
    else:
        send_event = True

    if send_event:
        try:
            active_win.module.handle_input(event, active_win.app_data, active_win.rect)
        except TypeError:
            active_win.module.handle_input(event, active_win.app_data)
