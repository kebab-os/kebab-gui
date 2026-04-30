from graphics import graphics as pygame
from datetime import datetime


def draw_windows(screen, open_wins, mx, my, close_icon, fullscreen_icon, windowed_icon):
    for i, w in enumerate(open_wins):
        is_act = i == (len(open_wins) - 1)
        w.draw(screen, mx, my, is_act, close_icon, fullscreen_icon, windowed_icon)


def draw_taskbar(screen, width, height, mx, my, open_wins, pinned_apps, apps_reg, start_icon):
    taskbar_bg = pygame.Rect(0, height - 50, width, 50)
    pygame.draw.rect(screen, (245, 245, 247), taskbar_bg)
    pygame.draw.rect(screen, (230, 230, 235), taskbar_bg, 1)
    pygame.draw.line(screen, (220, 220, 225), (0, height - 50), (width, height - 50), 1)

    s_r = pygame.Rect(8, height - 42, 36, 36)
    if start_icon:
        if s_r.collidepoint(mx, my):
            pygame.draw.rect(screen, (220, 220, 225), s_r, border_radius=8)
        screen.blit(start_icon, (s_r.x + (s_r.w - start_icon.get_width()) // 2, s_r.y + (s_r.h - start_icon.get_height()) // 2))

    run_names = [win.name for win in open_wins]
    active_app = open_wins[-1].name if open_wins else None
    for i, name in enumerate(pinned_apps):
        ix = 55 + i * 50
        ix_r = pygame.Rect(ix, height - 42, 40, 36)

        if name in apps_reg and apps_reg[name]["icon"]:
            if ix_r.collidepoint(mx, my):
                pygame.draw.rect(screen, (220, 220, 225), ix_r, border_radius=8)
            screen.blit(pygame.transform.scale(apps_reg[name]["icon"], (24, 24)), (ix + 8, height - 36))
            if name in run_names:
                is_active_app = name == active_app
                ind_w = 22 if is_active_app else 12
                ind_x = ix + (40 - ind_w) // 2
                ind_color = (72, 147, 255) if is_active_app else (120, 150, 200)
                pygame.draw.rect(screen, ind_color, (ind_x, height - 8, ind_w, 4), border_radius=3)


def draw_start_menu(screen, font, height, mx, my, start_open, start_search, apps_reg, shutdown_icon, logout_icon):
    if not start_open:
        return

    results = [n for n in apps_reg.keys() if start_search.lower() in n.lower()]
    items = results
    mh = len(items) * 44 + 110
    mr = pygame.Rect(8, height - 60 - mh, 210, mh)
    pygame.draw.rect(screen, (255, 255, 255), mr, border_radius=12)
    pygame.draw.rect(screen, (235, 235, 240), mr, 1, border_radius=12)

    search_r = pygame.Rect(mr.x + 8, mr.y + 8, 194, 34)
    pygame.draw.rect(screen, (246, 247, 250), search_r, border_radius=8)
    pygame.draw.rect(screen, (225, 228, 234), search_r, 1, border_radius=8)
    search_text = start_search if start_search else "Search apps..."
    search_col = (62, 70, 82) if start_search else (145, 150, 160)
    screen.blit(font.render(search_text, True, search_col), (search_r.x + 10, search_r.y + 7))

    for i, item in enumerate(items):
        it_r = pygame.Rect(mr.x + 8, mr.y + 50 + (i * 44), 194, 40)
        if it_r.collidepoint(mx, my):
            pygame.draw.rect(screen, (235, 235, 240), it_r, border_radius=8)
        ic = apps_reg[item]["icon"] if item in apps_reg else None
        if ic:
            screen.blit(pygame.transform.scale(ic, (18, 18)), (it_r.x + 12, it_r.y + 11))
        screen.blit(font.render(item.capitalize(), True, (45, 52, 54)), (it_r.x + 38, it_r.y + 9))

    # Always-visible icon-only action row.
    btn_y = mr.bottom - 48
    logout_r = pygame.Rect(mr.x + 118, btn_y, 40, 34)
    shutdown_r = pygame.Rect(mr.x + 162, btn_y, 40, 34)

    for r in (logout_r, shutdown_r):
        if r.collidepoint(mx, my):
            pygame.draw.rect(screen, (232, 238, 248), r, border_radius=8)
        else:
            pygame.draw.rect(screen, (244, 246, 250), r, border_radius=8)
        pygame.draw.rect(screen, (222, 228, 238), r, 1, border_radius=8)

    if logout_icon:
        screen.blit(logout_icon, (logout_r.x + (logout_r.w - logout_icon.get_width()) // 2, logout_r.y + (logout_r.h - logout_icon.get_height()) // 2))
    if shutdown_icon:
        screen.blit(shutdown_icon, (shutdown_r.x + (shutdown_r.w - shutdown_icon.get_width()) // 2, shutdown_r.y + (shutdown_r.h - shutdown_icon.get_height()) // 2))


def draw_clock(screen, font, width, height):
    time_str = datetime.now().strftime("%H:%M:%S")
    t_surf = font.render(time_str, True, (100, 100, 100))
    screen.blit(t_surf, (width - t_surf.get_width() - 12, height - 36))
