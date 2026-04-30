import configparser
import json
import os
import sys
import hashlib

from graphics import graphics as pygame


USERS_INI_FILE = "users/users.ini"
USERS_JSON_LEGACY_FILE = "users/users.json"
USER_STORAGE_ROOT = "storage/users"


def _safe_username(username):
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in str(username or "").strip())
    return safe or "user"


def _user_storage_dir(username):
    return os.path.join(USER_STORAGE_ROOT, _safe_username(username))


def _user_avatar_path(username):
    return os.path.join(_user_storage_dir(username), "avatar.png")


def _avatar_initials(display_name, username):
    source = str(display_name or username or "U").strip()
    parts = [part for part in source.replace("_", " ").split() if part]
    if not parts:
        return "U"
    initials = "".join(part[0] for part in parts[:2]).upper()
    return initials or source[:2].upper() or "U"


def _avatar_colors(username):
    digest = hashlib.sha1(_safe_username(username).encode("utf-8")).digest()
    bg = (70 + digest[0] % 120, 90 + digest[1] % 110, 130 + digest[2] % 90)
    fg = (245, 248, 252)
    return bg, fg


def _ensure_user_avatar(user):
    username = user.get("username", "user")
    display_name = user.get("display_name", username)
    avatar_path = user.get("avatar", "").strip() if isinstance(user.get("avatar"), str) else ""
    if not avatar_path:
        avatar_path = _user_avatar_path(username)
        user["avatar"] = avatar_path

    if os.path.exists(avatar_path) and os.path.getsize(avatar_path) > 0:
        return avatar_path

    os.makedirs(os.path.dirname(avatar_path), exist_ok=True)
    if not pygame.font.get_init():
        pygame.font.init()
    surface = pygame.Surface((128, 128), pygame.SRCALPHA)
    bg, fg = _avatar_colors(username)
    pygame.draw.circle(surface, bg, (64, 64), 64)
    initials = _avatar_initials(display_name, username)
    font = pygame.font.SysFont("Segoe UI", 44, bold=True)
    label = font.render(initials, True, fg)
    surface.blit(label, ((128 - label.get_width()) // 2, (128 - label.get_height()) // 2 - 2))
    pygame.image.save(surface, avatar_path)
    return avatar_path


def _default_users():
    return [
        {
            "username": "admin",
            "password": "admin",
            "display_name": "Administrator",
            "avatar": _user_avatar_path("admin"),
        }
    ]


def _write_users_ini(users):
    parser = configparser.ConfigParser()
    for idx, user in enumerate(users, start=1):
        section = f"user:{idx}"
        parser[section] = {
            "username": user.get("username", ""),
            "password": user.get("password", ""),
            "display_name": user.get("display_name", user.get("username", "")),
            "avatar": user.get("avatar", _user_avatar_path(user.get("username", ""))),
        }

    os.makedirs(os.path.dirname(USERS_INI_FILE), exist_ok=True)
    with open(USERS_INI_FILE, "w", encoding="utf-8") as f:
        parser.write(f)


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
        avatar = str(entry.get("avatar", _user_avatar_path(username))).strip() or _user_avatar_path(username)
        if username:
            normalized.append(
                {
                    "username": username,
                    "password": password,
                    "display_name": display_name,
                    "avatar": avatar,
                }
            )
    return normalized


def _load_users_from_ini():
    parser = configparser.ConfigParser()
    parser.read(USERS_INI_FILE, encoding="utf-8")

    users = []
    for section in parser.sections():
        if not section.lower().startswith("user:"):
            continue

        username = parser.get(section, "username", fallback="").strip()
        password = parser.get(section, "password", fallback="")
        display_name = parser.get(section, "display_name", fallback=username).strip() or username
        avatar = parser.get(section, "avatar", fallback=_user_avatar_path(username)).strip() or _user_avatar_path(username)
        if username:
            users.append(
                {
                    "username": username,
                    "password": password,
                    "display_name": display_name,
                    "avatar": avatar,
                }
            )

    return users


def _load_users_from_json_legacy():
    try:
        with open(USERS_JSON_LEGACY_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return []
    return _normalize_users(raw)


def load_users():
    os.makedirs(os.path.dirname(USERS_INI_FILE), exist_ok=True)

    users = []
    if os.path.exists(USERS_INI_FILE) and os.path.getsize(USERS_INI_FILE) > 0:
        users = _load_users_from_ini()
    elif os.path.exists(USERS_JSON_LEGACY_FILE) and os.path.getsize(USERS_JSON_LEGACY_FILE) > 0:
        users = _load_users_from_json_legacy()

    if not users:
        users = _default_users()

    for user in users:
        _ensure_user_avatar(user)

    _write_users_ini(users)

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

    avatar_cache = {}

    def _load_avatar(path):
        if not path:
            return None
        if path not in avatar_cache:
            try:
                avatar_cache[path] = pygame.transform.smoothscale(pygame.image.load(path).convert_alpha(), (28, 28))
            except Exception:
                avatar_cache[path] = None
        return avatar_cache[path]

    # Precompute a higher-quality blurred background from the wallpaper (cached)
    blurred_bg = None
    if wallpaper:
        try:
            # Multiple downscale/upscale passes for a stronger, smoother blur
            blurred_bg = wallpaper.copy()
            for pass_scale in (0.08, 0.18, 0.32):
                small_w = max(2, int(width * pass_scale))
                small_h = max(2, int(height * pass_scale))
                tmp = pygame.transform.smoothscale(blurred_bg, (small_w, small_h))
                blurred_bg = pygame.transform.smoothscale(tmp, (width, height))
        except Exception:
            blurred_bg = None
        # Precompute a higher-quality blurred background from the wallpaper (cached).
        # Prefer a true separable Gaussian blur via numpy + surfarray when available;
        # otherwise fall back to a multi-pass averaged upscale which approximates blur.
        def _blur_surface(src_surf, radius=10):
            # Try numpy-based separable gaussian blur
            try:
                import numpy as np

                arr = pygame.surfarray.array3d(src_surf).astype(np.float32)
                # arr shape: (w, h, 3) -> transpose to (h, w, 3) for easier ops
                arr = np.transpose(arr, (1, 0, 2))

                def _gaussian_kernel(r):
                    sigma = max(0.5, r / 2.0)
                    size = int(r) * 2 + 1
                    x = np.arange(size) - (size // 2)
                    k = np.exp(-(x ** 2) / (2 * sigma * sigma))
                    k = k / k.sum()
                    return k.astype(np.float32)

                k = _gaussian_kernel(radius)

                # Pad and convolve separably on rows and columns
                pad_w = k.size // 2
                # horizontal pass
                padded = np.pad(arr, ((0, 0), (pad_w, pad_w), (0, 0)), mode="reflect")
                tmp = np.empty_like(arr)
                for i in range(arr.shape[0]):
                    for c in range(3):
                        tmp[i, :, c] = np.convolve(padded[i, :, c], k, mode="valid")

                # vertical pass
                padded = np.pad(tmp, ((pad_w, pad_w), (0, 0), (0, 0)), mode="reflect")
                out = np.empty_like(tmp)
                for j in range(tmp.shape[1]):
                    for c in range(3):
                        out[:, j, c] = np.convolve(padded[:, j, c], k, mode="valid")

                out = np.clip(out, 0, 255).astype(np.uint8)
                out = np.transpose(out, (1, 0, 2))
                surf = pygame.Surface((src_surf.get_width(), src_surf.get_height()))
                pygame.surfarray.blit_array(surf, out)
                # Preserve alpha if present
                try:
                    alpha = pygame.surfarray.array_alpha(src_surf)
                    alpha = alpha.astype(np.float32)
                    # blur alpha similarly using separable kernel
                    padded = np.pad(alpha, (pad_w, pad_w), mode="reflect")
                    tmpa = np.empty_like(alpha)
                    for i in range(alpha.shape[0]):
                        tmpa[i, :] = np.convolve(padded[i, :], k, mode="valid")
                    padded = np.pad(tmpa, (pad_w, pad_w), mode="reflect")
                    outa = np.empty_like(tmpa)
                    for j in range(tmpa.shape[1]):
                        outa[:, j] = np.convolve(padded[:, j], k, mode="valid")
                    outa = np.clip(outa, 0, 255).astype(np.uint8)
                    pygame.surfarray.pixels_alpha(surf)[:, :] = outa
                except Exception:
                    pass

                return surf
            except Exception:
                # numpy not available or blur failed — fall back to multi-pass averaging
                try:
                    scales = (0.04, 0.08, 0.16, 0.28)
                    acc = pygame.Surface((width, height), pygame.SRCALPHA)
                    weight = int(200 / max(1, len(scales)))
                    for s in scales:
                        sw = max(2, int(width * s))
                        sh = max(2, int(height * s))
                        tmp = pygame.transform.smoothscale(src_surf, (sw, sh))
                        tmp2 = pygame.transform.smoothscale(tmp, (width, height))
                        tmp2.set_alpha(weight)
                        acc.blit(tmp2, (0, 0))
                    return acc
                except Exception:
                    return None

        blurred_bg = None
        if wallpaper:
            try:
                blurred_bg = _blur_surface(wallpaper, radius=10)
            except Exception:
                blurred_bg = None

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

        if blurred_bg:
            screen.blit(blurred_bg, (0, 0))
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            overlay.fill((18, 24, 32, 64))
            screen.blit(overlay, (0, 0))
        elif wallpaper:
            # Fallback: wallpaper present but blur failed
            screen.blit(wallpaper, (0, 0))
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            overlay.fill((18, 24, 32, 90))
            screen.blit(overlay, (0, 0))
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

            avatar = _load_avatar(user.get("avatar", ""))
            avatar_box = pygame.Rect(item_r.x + 6, item_r.y + 7, 28, 28)
            if avatar:
                screen.blit(avatar, avatar_box.topleft)
            else:
                pygame.draw.circle(screen, (116, 146, 196), avatar_box.center, 10)
            label = user_font.render(user.get("display_name", user["username"]), True, (30, 38, 50))
            screen.blit(label, (item_r.x + 42, item_r.y + 9))

        if cursor_img:
            screen.blit(cursor_img, (mx, my))

        pygame.display.flip()
        clock.tick(60)
