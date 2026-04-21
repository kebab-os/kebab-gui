import json
import os
import sys

import pygame


USERS_FILE = "src/users/users.json"


def _default_users():
    return {
        "users": [
            {
                "username": "admin",
                "password": "admin",
                "display_name": "Administrator"
            }
        ]
    }


def _normalize_users(raw):
    if isinstance(raw, list):
        users = raw
    elif isinstance(raw, dict):
        users = raw.get("users", [])
    else:
        users = []

    normalized = []
    for entry in users:
        if not isinstance(entry, dict):
            continue
        username = str(entry.get("username", "")).strip()
        password = str(entry.get("password", ""))
        display_name = str(entry.get("display_name", username)).strip() or username
        if username:
            normalized.append(
                {
                    "username": username,
                    "password": password,
                    "display_name": display_name,
                }
            )
    return normalized


def load_users():
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)

    if not os.path.exists(USERS_FILE) or os.path.getsize(USERS_FILE) == 0:
        defaults = _default_users()
        with open(USERS_FILE, "w") as f:
            json.dump(defaults, f, indent=2)
        return defaults["users"]

    try:
        with open(USERS_FILE, "r") as f:
            raw = json.load(f)
    except Exception:
        defaults = _default_users()
        with open(USERS_FILE, "w") as f:
            json.dump(defaults, f, indent=2)
        return defaults["users"]

    users = _normalize_users(raw)
    if not users:
        defaults = _default_users()
        with open(USERS_FILE, "w") as f:
            json.dump(defaults, f, indent=2)
        return defaults["users"]

    return users


def run_login_screen(screen, width, height, wallpaper=None, cursor_img=None):
    users = load_users()
    selected_idx = 0
    password = ""
    error_msg = ""

    title_font = pygame.font.SysFont("Segoe UI", 44, bold=True)
    subtitle_font = pygame.font.SysFont("Segoe UI", 18)
    user_font = pygame.font.SysFont("Segoe UI", 18, bold=True)
    small_font = pygame.font.SysFont("Segoe UI", 14)
    pwd_font = pygame.font.SysFont("Consolas", 22)
    clock = pygame.time.Clock()

    while True:
        mx, my = pygame.mouse.get_pos()

        # Bottom-left user list geometry
        btn_x = 26
        btn_w = 250
        btn_h = 42
        btn_gap = 8
        list_h = len(users) * btn_h + max(0, len(users) - 1) * btn_gap
        list_top = height - 26 - list_h

        center_x = width // 2
        center_y = height // 2 - 12

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_LEFT):
                    selected_idx = (selected_idx - 1) % len(users)
                    password = ""
                    error_msg = ""
                elif event.key in (pygame.K_DOWN, pygame.K_RIGHT, pygame.K_TAB):
                    selected_idx = (selected_idx + 1) % len(users)
                    password = ""
                    error_msg = ""
                elif event.key == pygame.K_BACKSPACE:
                    password = password[:-1]
                elif event.key == pygame.K_RETURN:
                    selected = users[selected_idx]
                    if password == selected.get("password", ""):
                        return selected
                    error_msg = "Incorrect password"
                    password = ""
                elif event.unicode and event.unicode.isprintable():
                    password += event.unicode

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, _ in enumerate(users):
                    item_r = pygame.Rect(btn_x, list_top + i * (btn_h + btn_gap), btn_w, btn_h)
                    if item_r.collidepoint(event.pos):
                        selected_idx = i
                        password = ""
                        error_msg = ""

        if wallpaper:
            screen.blit(wallpaper, (0, 0))
        else:
            screen.fill((224, 228, 234))

        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((18, 24, 32, 90))
        screen.blit(overlay, (0, 0))

        # Center section (no background panel)
        selected = users[selected_idx]
        display_name = selected.get("display_name", selected["username"])

        name_surf = title_font.render(display_name, True, (246, 249, 255))
        screen.blit(name_surf, (center_x - name_surf.get_width() // 2, center_y - 102))

        sub = subtitle_font.render("Enter password", True, (205, 214, 230))
        screen.blit(sub, (center_x - sub.get_width() // 2, center_y - 48))

        # Input with minimal chrome (line only)
        input_w = 360
        input_h = 48
        pwd_r = pygame.Rect(center_x - input_w // 2, center_y - 2, input_w, input_h)
        line_col = (164, 188, 235) if password else (188, 198, 214)
        pygame.draw.line(screen, line_col, (pwd_r.x, pwd_r.bottom), (pwd_r.right, pwd_r.bottom), 2)

        hidden = "•" * len(password)
        cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
        pwd_surf = pwd_font.render(hidden + cursor, True, (244, 247, 255))
        screen.blit(pwd_surf, (pwd_r.x + 6, pwd_r.y + 10))

        hint = small_font.render("Press Enter to sign in", True, (190, 202, 220))
        screen.blit(hint, (center_x - hint.get_width() // 2, pwd_r.bottom + 12))

        if error_msg:
            err = subtitle_font.render(error_msg, True, (255, 145, 145))
            screen.blit(err, (center_x - err.get_width() // 2, pwd_r.bottom + 38))

        # Bottom-left user list buttons
        for i, user in enumerate(users):
            item_r = pygame.Rect(btn_x, list_top + i * (btn_h + btn_gap), btn_w, btn_h)
            if i == selected_idx:
                pygame.draw.rect(screen, (226, 237, 255), item_r, border_radius=10)
                pygame.draw.rect(screen, (130, 171, 236), item_r, 1, border_radius=10)
            elif item_r.collidepoint((mx, my)):
                pygame.draw.rect(screen, (240, 246, 255), item_r, border_radius=10)

            pygame.draw.circle(screen, (116, 146, 196), (item_r.x + 20, item_r.y + item_r.h // 2), 10)
            label = user_font.render(user.get("display_name", user["username"]), True, (30, 38, 50))
            screen.blit(label, (item_r.x + 40, item_r.y + 9))

        if cursor_img:
            screen.blit(cursor_img, (mx, my))

        pygame.display.flip()
        clock.tick(60)
