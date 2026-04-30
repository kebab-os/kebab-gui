from graphics import graphics as pygame


def _ensure_state(data):
    data.setdefault("buffer", "")
    data.setdefault("cursor", len(data["buffer"]))
    data.setdefault("scroll_y", 0)
    data.setdefault("preferred_col", None)
    data.setdefault("mouse_selecting", False)
    data["cursor"] = max(0, min(data["cursor"], len(data["buffer"])))


def _line_starts(text):
    starts = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            starts.append(i + 1)
    return starts


def _index_to_line_col(text, idx):
    idx = max(0, min(idx, len(text)))
    starts = _line_starts(text)
    line = 0
    for i, st in enumerate(starts):
        if st <= idx:
            line = i
        else:
            break
    return line, idx - starts[line], starts


def _line_col_to_index(text, line, col):
    starts = _line_starts(text)
    line = max(0, min(line, len(starts) - 1))
    line_start = starts[line]
    if line + 1 < len(starts):
        line_end = starts[line + 1] - 1
    else:
        line_end = len(text)
    return max(line_start, min(line_start + max(0, col), line_end))


def _content_rect(window_rect):
    return pygame.Rect(window_rect.x + 5, window_rect.y + 36, window_rect.w - 10, window_rect.h - 41)


def _ensure_cursor_visible(data, window_rect=None):
    line_h = 18
    if window_rect is None:
        view_h = 260
    else:
        view_h = max(80, _content_rect(window_rect).h - 8)
    line, _, _ = _index_to_line_col(data["buffer"], data["cursor"])
    y = line * line_h
    if y < data["scroll_y"]:
        data["scroll_y"] = y
    elif y + line_h > data["scroll_y"] + view_h:
        data["scroll_y"] = y + line_h - view_h
    data["scroll_y"] = max(0, data["scroll_y"])


def handle_input(event, data, window_rect=None):
    _ensure_state(data)
    line_h = 18

    if event.type == pygame.MOUSEWHEEL:
        data["scroll_y"] = max(0, data["scroll_y"] - event.y * line_h * 3)
        return

    if event.type != pygame.KEYDOWN:
        return

    mods = pygame.key.get_mods()
    ctrl = bool(mods & pygame.KMOD_CTRL)

    if ctrl and event.key == pygame.K_v:
        pasted = pygame.scrap.get(pygame.SCRAP_TEXT)
        if pasted:
            txt = pasted.decode("utf-8", errors="ignore").replace("\r\n", "\n").rstrip("\x00")
            data["buffer"] = data["buffer"][:data["cursor"]] + txt + data["buffer"][data["cursor"]:]
            data["cursor"] += len(txt)
            _ensure_cursor_visible(data, window_rect)
        return

    if ctrl and event.key == pygame.K_a:
        data["cursor"] = len(data["buffer"])
        return

    if event.key == pygame.K_BACKSPACE:
        if data["cursor"] > 0:
            data["buffer"] = data["buffer"][:data["cursor"] - 1] + data["buffer"][data["cursor"]:]
            data["cursor"] -= 1
            _ensure_cursor_visible(data, window_rect)
        return

    if event.key == pygame.K_DELETE:
        if data["cursor"] < len(data["buffer"]):
            data["buffer"] = data["buffer"][:data["cursor"]] + data["buffer"][data["cursor"] + 1:]
        return

    if event.key == pygame.K_RETURN:
        data["buffer"] = data["buffer"][:data["cursor"]] + "\n" + data["buffer"][data["cursor"]:]
        data["cursor"] += 1
        _ensure_cursor_visible(data, window_rect)
        return

    if event.key == pygame.K_LEFT:
        data["cursor"] = max(0, data["cursor"] - 1)
        _ensure_cursor_visible(data, window_rect)
        return

    if event.key == pygame.K_RIGHT:
        data["cursor"] = min(len(data["buffer"]), data["cursor"] + 1)
        _ensure_cursor_visible(data, window_rect)
        return

    if event.key == pygame.K_UP:
        line, col, _ = _index_to_line_col(data["buffer"], data["cursor"])
        data["cursor"] = _line_col_to_index(data["buffer"], line - 1, col)
        _ensure_cursor_visible(data, window_rect)
        return

    if event.key == pygame.K_DOWN:
        line, col, _ = _index_to_line_col(data["buffer"], data["cursor"])
        data["cursor"] = _line_col_to_index(data["buffer"], line + 1, col)
        _ensure_cursor_visible(data, window_rect)
        return

    if event.unicode.isprintable():
        data["buffer"] = data["buffer"][:data["cursor"]] + event.unicode + data["buffer"][data["cursor"]:]
        data["cursor"] += len(event.unicode)
        _ensure_cursor_visible(data, window_rect)


def draw_content(surface, rect, data, is_active):
    _ensure_state(data)
    font = pygame.font.SysFont("Consolas", 14)
    line_h = 18
    inner = pygame.Rect(rect.x + 5, rect.y + 35, rect.w - 10, rect.h - 40)
    pygame.draw.rect(surface, (255, 255, 255), inner)
    surface.set_clip(inner)

    lines = data["buffer"].split("\n")
    start_y = inner.y + 5 - data["scroll_y"]
    cursor_line, cursor_col, _ = _index_to_line_col(data["buffer"], data["cursor"])

    for index, line in enumerate(lines):
        y = start_y + (index * line_h)
        if y + line_h < inner.y - 20 or y > inner.bottom + 20:
            continue
        surface.blit(font.render(line or " ", True, (45, 50, 62)), (inner.x + 6, y))
        if is_active and index == cursor_line and (pygame.time.get_ticks() // 500) % 2 == 0:
            cursor_x = inner.x + 6 + font.size(line[:cursor_col])[0]
            pygame.draw.line(surface, (35, 35, 35), (cursor_x, y), (cursor_x, y + line_h - 2), 1)

    surface.set_clip(None)