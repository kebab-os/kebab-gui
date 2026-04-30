from graphics import graphics as pygame

import subprocess

import os

import sys



_MAX_LINES = 1200





def _ensure_state(data):

    data.setdefault("command", "")

    data.setdefault("output", [])

    data.setdefault("history", [])

    data.setdefault("history_index", -1)

    data.setdefault("scroll_offset", 0)

    data.setdefault("cwd", os.getcwd())

    data.setdefault("initialized", False)



    if not data["initialized"]:

        data["output"] = [

            "[info] kebabOS Terminal",

            "[muted] Type commands and press Enter.",

            "[muted] Built-ins: cd, clear, cls, pwd",

            "",

        ]

        data["initialized"] = True





def _append_lines(data, lines):

    output = data.get("output", [])

    output.extend(lines)

    data["output"] = output[-_MAX_LINES:]





def _prompt(data):

    cwd = data.get("cwd", os.getcwd())

    base = os.path.basename(cwd.rstrip("\\/")) or cwd

    return f"{base}> "





def _line_color(line):

    if line.startswith("$ "):

        return (124, 220, 255)

    if line.startswith("[error]"):

        return (255, 132, 132)

    if line.startswith("[info]"):

        return (147, 255, 168)

    if line.startswith("[muted]"):

        return (140, 146, 168)

    return (222, 227, 240)





def _line_text(line):

    for tag in ("[error] ", "[info] ", "[muted] "):

        if line.startswith(tag):

            return line[len(tag):]

    return line





def _draw_gradient(surface, rect, top, bottom):

    if rect.h <= 1:

        return

    for i in range(rect.h):

        t = i / float(rect.h - 1)

        color = (

            int(top[0] + (bottom[0] - top[0]) * t),

            int(top[1] + (bottom[1] - top[1]) * t),

            int(top[2] + (bottom[2] - top[2]) * t),

        )

        pygame.draw.line(surface, color, (rect.x, rect.y + i), (rect.right - 1, rect.y + i))





def _wrap_line(text, font, max_width):

    if text == "":

        return [""]

    words = text.split(" ")

    lines = []

    current = ""

    for word in words:

        candidate = word if not current else f"{current} {word}"

        if font.size(candidate)[0] <= max_width:

            current = candidate

        else:

            if current:

                lines.append(current)

            # Hard-wrap very long single tokens.

            token = word

            while font.size(token)[0] > max_width and len(token) > 1:

                cut = max(1, int(len(token) * max_width / max(1, font.size(token)[0])))

                lines.append(token[:cut])

                token = token[cut:]

            current = token

    if current or not lines:

        lines.append(current)

    return lines





def draw_content(surface, rect, data, is_active):

    """Render a modern terminal UI with rounded panels and clean spacing."""

    _ensure_state(data)



    bg_rect = pygame.Rect(rect.x, rect.y, rect.w, rect.h)

    _draw_gradient(surface, bg_rect, (15, 20, 35), (22, 28, 50))



    panel = pygame.Rect(rect.x + 10, rect.y + 10, rect.w - 20, rect.h - 20)

    shadow = panel.move(3, 4)

    pygame.draw.rect(surface, (10, 12, 22), shadow, border_radius=12)

    pygame.draw.rect(surface, (20, 24, 40), panel, border_radius=12)

    pygame.draw.rect(surface, (56, 64, 92), panel, width=1, border_radius=12)



    header_h = 36

    header = pygame.Rect(panel.x, panel.y, panel.w, header_h)

    _draw_gradient(surface, header, (34, 40, 64), (26, 31, 50))



    # Window controls.

    dots_y = header.centery

    pygame.draw.circle(surface, (255, 95, 87), (header.x + 18, dots_y), 5)

    pygame.draw.circle(surface, (254, 188, 46), (header.x + 36, dots_y), 5)

    pygame.draw.circle(surface, (40, 201, 64), (header.x + 54, dots_y), 5)



    title_font = pygame.font.SysFont("Segoe UI Semibold", 14)

    title = title_font.render("Terminal", True, (214, 221, 246))

    surface.blit(title, (header.x + 76, header.y + 10))



    cwd_font = pygame.font.SysFont("Consolas", 12)

    cwd_text = cwd_font.render(data.get("cwd", ""), True, (140, 146, 168))

    cwd_x = max(header.x + 230, header.right - cwd_text.get_width() - 12)

    surface.blit(cwd_text, (cwd_x, header.y + 11))



    output_rect = pygame.Rect(panel.x + 12, header.bottom + 8, panel.w - 24, panel.h - header_h - 66)

    pygame.draw.rect(surface, (14, 18, 30), output_rect, border_radius=10)

    pygame.draw.rect(surface, (45, 52, 78), output_rect, width=1, border_radius=10)



    input_rect = pygame.Rect(panel.x + 12, panel.bottom - 48, panel.w - 24, 36)

    pygame.draw.rect(surface, (17, 21, 35), input_rect, border_radius=10)

    pygame.draw.rect(surface, (74, 155, 255), input_rect, width=1, border_radius=10)



    text_font = pygame.font.SysFont("Consolas", 14)

    line_h = 18

    max_text_width = output_rect.w - 24



    wrapped = []

    for raw in data.get("output", []):

        stripped = _line_text(raw)

        color = _line_color(raw)

        for piece in _wrap_line(stripped, text_font, max_text_width):

            wrapped.append((piece, color))



    visible = max(1, (output_rect.h - 10) // line_h)

    max_scroll = max(0, len(wrapped) - visible)

    data["scroll_offset"] = max(0, min(data.get("scroll_offset", 0), max_scroll))

    start = max(0, len(wrapped) - visible - data["scroll_offset"])



    y = output_rect.y + 6

    for line, color in wrapped[start : start + visible]:

        surface.blit(text_font.render(line, True, color), (output_rect.x + 10, y))

        y += line_h



    if max_scroll > 0:

        track = pygame.Rect(output_rect.right - 8, output_rect.y + 6, 4, output_rect.h - 12)

        pygame.draw.rect(surface, (34, 39, 60), track, border_radius=2)

        thumb_h = max(18, int(track.h * (visible / max(1, len(wrapped)))))

        thumb_y = track.y + int((track.h - thumb_h) * (data["scroll_offset"] / max_scroll))

        pygame.draw.rect(surface, (95, 110, 160), (track.x, thumb_y, track.w, thumb_h), border_radius=2)



    prompt = _prompt(data)

    cmd = data.get("command", "")

    prompt_surface = text_font.render(prompt, True, (124, 220, 255))

    surface.blit(prompt_surface, (input_rect.x + 10, input_rect.y + 9))

    cmd_x = input_rect.x + 10 + prompt_surface.get_width()

    surface.blit(text_font.render(cmd, True, (231, 236, 250)), (cmd_x, input_rect.y + 9))



    if is_active and (pygame.time.get_ticks() // 500) % 2 == 0:

        cursor_x = cmd_x + text_font.size(cmd)[0]

        pygame.draw.line(surface, (124, 220, 255), (cursor_x, input_rect.y + 8), (cursor_x, input_rect.y + 26), 2)





def _run_command(cmd, data):

    cwd = data.get("cwd", os.getcwd())



    if cmd in ("clear", "cls"):

        data["output"] = []

        data["scroll_offset"] = 0

        return



    if cmd == "pwd":

        _append_lines(data, [cwd, ""])

        return



    if cmd.lower().startswith("cd"):

        target = cmd[2:].strip().strip('"')

        if not target:

            _append_lines(data, [cwd, ""])

            return

        if target == "~":

            target_path = os.path.expanduser("~")

        else:

            target_path = os.path.abspath(os.path.join(cwd, target))

        if os.path.isdir(target_path):

            data["cwd"] = target_path

            _append_lines(data, [f"[info] cwd -> {target_path}", ""])

        else:

            _append_lines(data, [f"[error] Directory not found: {target}", ""])

        return



    try:

        kwargs = {

            "shell": True,

            "capture_output": True,

            "text": True,

            "timeout": 20,

            "cwd": cwd,

        }

        if sys.platform == "win32":

            kwargs["executable"] = os.environ.get("COMSPEC", None)

        result = subprocess.run(cmd, **kwargs)



        lines = []

        if result.stdout:

            lines.extend(result.stdout.rstrip("\n").split("\n"))

        if result.stderr:

            lines.extend([f"[error] {line}" for line in result.stderr.rstrip("\n").split("\n")])

        if result.returncode != 0 and not result.stderr:

            lines.append(f"[error] Command exited with code {result.returncode}")

        if not lines:

            lines.append("[muted] Command completed")

        lines.append("")

        _append_lines(data, lines)

    except subprocess.TimeoutExpired:

        _append_lines(data, ["[error] Command timed out after 20 seconds", ""])

    except Exception as exc:

        _append_lines(data, [f"[error] {exc}", ""])





def handle_input(event, data, rect):

    """Handle keyboard and wheel input for the terminal."""

    _ensure_state(data)



    if event.type == pygame.MOUSEWHEEL:

        if event.y > 0:

            data["scroll_offset"] = data.get("scroll_offset", 0) + 4

        elif event.y < 0:

            data["scroll_offset"] = max(0, data.get("scroll_offset", 0) - 4)

        return



    if event.type != pygame.KEYDOWN:

        return



    key = event.key

    history = data.get("history", [])

    history_index = data.get("history_index", -1)



    if key == pygame.K_UP and history:

        if history_index < len(history) - 1:

            history_index += 1

            data["history_index"] = history_index

            data["command"] = history[history_index]

        return



    if key == pygame.K_DOWN and history:

        if history_index > 0:

            history_index -= 1

            data["history_index"] = history_index

            data["command"] = history[history_index]

        elif history_index == 0:

            data["history_index"] = -1

            data["command"] = ""

        return



    if key == pygame.K_RETURN:

        cmd = data.get("command", "").strip()

        if cmd:

            _append_lines(data, [f"$ {cmd}"])

            if not history or history[0] != cmd:

                history.insert(0, cmd)

            data["history"] = history[:200]

            data["history_index"] = -1

            _run_command(cmd, data)

        data["command"] = ""

        data["scroll_offset"] = 0

        return



    if key == pygame.K_BACKSPACE:

        data["command"] = data.get("command", "")[:-1]

        return



    if key == pygame.K_PAGEUP:

        data["scroll_offset"] = data.get("scroll_offset", 0) + 10

        return



    if key == pygame.K_PAGEDOWN:

        data["scroll_offset"] = max(0, data.get("scroll_offset", 0) - 10)

        return



    if key == pygame.K_ESCAPE:

        data["command"] = ""

        data["history_index"] = -1

        return



    if key == pygame.K_l and (pygame.key.get_mods() & pygame.KMOD_CTRL):

        data["output"] = []

        data["scroll_offset"] = 0

        return



    if event.unicode and event.unicode.isprintable():

        data["command"] = data.get("command", "") + event.unicode

