import pygame


def _ensure_state(data):
    data.setdefault("buffer", "")
    data.setdefault("cursor", len(data["buffer"]))
    data.setdefault("sel_anchor", None)
    data.setdefault("sel_focus", None)
    data.setdefault("preferred_col", None)
    data.setdefault("scroll_y", 0)
    data.setdefault("mouse_selecting", False)
    data.setdefault("undo", [])
    data.setdefault("redo", [])
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


def _selection_range(data):
    a = data.get("sel_anchor")
    b = data.get("sel_focus")
    if a is None or b is None or a == b:
        return None
    return (min(a, b), max(a, b))


def _clear_selection(data):
    data["sel_anchor"] = None
    data["sel_focus"] = None


def _set_cursor(data, pos, shift=False):
    data["cursor"] = max(0, min(pos, len(data["buffer"])))
    if shift:
        if data["sel_anchor"] is None:
            data["sel_anchor"] = data["cursor"]
        data["sel_focus"] = data["cursor"]
    else:
        _clear_selection(data)


def _push_undo(data):
    data["undo"].append((data["buffer"], data["cursor"], data["sel_anchor"], data["sel_focus"]))
    if len(data["undo"]) > 100:
        data["undo"].pop(0)


def _apply_snapshot(data, snap):
    data["buffer"], data["cursor"], data["sel_anchor"], data["sel_focus"] = snap
    data["cursor"] = max(0, min(data["cursor"], len(data["buffer"])))


def _undo(data):
    if not data["undo"]:
        return
    data["redo"].append((data["buffer"], data["cursor"], data["sel_anchor"], data["sel_focus"]))
    _apply_snapshot(data, data["undo"].pop())


def _redo(data):
    if not data["redo"]:
        return
    data["undo"].append((data["buffer"], data["cursor"], data["sel_anchor"], data["sel_focus"]))
    _apply_snapshot(data, data["redo"].pop())


def _delete_selection(data):
    sel = _selection_range(data)
    if not sel:
        return False
    s, e = sel
    data["buffer"] = data["buffer"][:s] + data["buffer"][e:]
    data["cursor"] = s
    _clear_selection(data)
    return True


def _insert_text(data, text):
    _push_undo(data)
    data["redo"].clear()
    _delete_selection(data)
    c = data["cursor"]
    data["buffer"] = data["buffer"][:c] + text + data["buffer"][c:]
    data["cursor"] = c + len(text)


def _is_word_char(ch):
    return ch.isalnum() or ch == "_"


def _move_word_left(text, idx):
    i = max(0, idx)
    while i > 0 and text[i - 1].isspace():
        i -= 1
    while i > 0 and _is_word_char(text[i - 1]):
        i -= 1
    return i


def _move_word_right(text, idx):
    i = min(len(text), idx)
    while i < len(text) and text[i].isspace():
        i += 1
    while i < len(text) and _is_word_char(text[i]):
        i += 1
    return i


def _delete_word_left(data):
    if _selection_range(data):
        _push_undo(data)
        data["redo"].clear()
        _delete_selection(data)
        return
    c = data["cursor"]
    n = _move_word_left(data["buffer"], c)
    if n != c:
        _push_undo(data)
        data["redo"].clear()
        data["buffer"] = data["buffer"][:n] + data["buffer"][c:]
        data["cursor"] = n


def _delete_word_right(data):
    if _selection_range(data):
        _push_undo(data)
        data["redo"].clear()
        _delete_selection(data)
        return
    c = data["cursor"]
    n = _move_word_right(data["buffer"], c)
    if n != c:
        _push_undo(data)
        data["redo"].clear()
        data["buffer"] = data["buffer"][:c] + data["buffer"][n:]


def _content_rect(window_rect):
    return pygame.Rect(window_rect.x + 5, window_rect.y + 36, window_rect.w - 10, window_rect.h - 41)


def _index_from_mouse(data, window_rect, mx, my, font, line_h):
    crect = _content_rect(window_rect)
    tx = crect.x + 5
    ty = crect.y + 4
    rel_y = my - ty + data["scroll_y"]
    lines = data["buffer"].split("\n")
    line = max(0, min(len(lines) - 1, rel_y // line_h if line_h else 0))
    line_text = lines[line]
    px = max(0, mx - tx)
    col = 0
    for i in range(len(line_text) + 1):
        if font.size(line_text[:i])[0] >= px:
            col = i
            break
        col = i
    return _line_col_to_index(data["buffer"], line, col)


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
    font = pygame.font.SysFont("Consolas", 14)
    line_h = 18

    if event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1 and window_rect is not None:
            crect = _content_rect(window_rect)
            if crect.collidepoint(event.pos):
                idx = _index_from_mouse(data, window_rect, event.pos[0], event.pos[1], font, line_h)
                data["cursor"] = idx
                data["sel_anchor"] = idx
                data["sel_focus"] = idx
                data["mouse_selecting"] = True
        return

    if event.type == pygame.MOUSEBUTTONUP:
        if event.button == 1:
            data["mouse_selecting"] = False
        return

    if event.type == pygame.MOUSEMOTION:
        if data.get("mouse_selecting") and window_rect is not None:
            idx = _index_from_mouse(data, window_rect, event.pos[0], event.pos[1], font, line_h)
            data["cursor"] = idx
            data["sel_focus"] = idx
            _ensure_cursor_visible(data, window_rect)
        return

    if event.type == pygame.MOUSEWHEEL:
        data["scroll_y"] = max(0, data["scroll_y"] - event.y * line_h * 3)
        return

    if event.type != pygame.KEYDOWN:
        return

    mods = pygame.key.get_mods()
    ctrl = bool(mods & pygame.KMOD_CTRL)
    shift = bool(mods & pygame.KMOD_SHIFT)

    if ctrl and event.key == pygame.K_a:
        data["sel_anchor"] = 0
        data["sel_focus"] = len(data["buffer"])
        data["cursor"] = len(data["buffer"])
        return

    if ctrl and event.key == pygame.K_c:
        sel = _selection_range(data)
        if sel:
            s, e = sel
            pygame.scrap.put(pygame.SCRAP_TEXT, data["buffer"][s:e].encode("utf-8"))
        return

    if ctrl and event.key == pygame.K_x:
        sel = _selection_range(data)
        if sel:
            s, e = sel
            pygame.scrap.put(pygame.SCRAP_TEXT, data["buffer"][s:e].encode("utf-8"))
            _push_undo(data)
            data["redo"].clear()
            _delete_selection(data)
        return

    if ctrl and event.key == pygame.K_v:
        pasted = pygame.scrap.get(pygame.SCRAP_TEXT)
        if pasted:
            txt = pasted.decode("utf-8", errors="ignore").replace("\r\n", "\n").rstrip("\x00")
            _insert_text(data, txt)
            _ensure_cursor_visible(data, window_rect)
        return

    if ctrl and event.key == pygame.K_z:
        _undo(data)
        _ensure_cursor_visible(data, window_rect)
        return

    if ctrl and event.key == pygame.K_y:
        _redo(data)
        _ensure_cursor_visible(data, window_rect)
        return

    if event.key == pygame.K_LEFT:
        if ctrl:
            n = _move_word_left(data["buffer"], data["cursor"])
        else:
            n = max(0, data["cursor"] - 1)
        if shift:
            if data["sel_anchor"] is None:
                data["sel_anchor"] = data["cursor"]
            data["cursor"] = n
            data["sel_focus"] = n
        else:
            data["cursor"] = n
            _clear_selection(data)
        data["preferred_col"] = None
        _ensure_cursor_visible(data, window_rect)
        return

    if event.key == pygame.K_RIGHT:
        if ctrl:
            n = _move_word_right(data["buffer"], data["cursor"])
        else:
            n = min(len(data["buffer"]), data["cursor"] + 1)
        if shift:
            if data["sel_anchor"] is None:
                data["sel_anchor"] = data["cursor"]
            data["cursor"] = n
            data["sel_focus"] = n
        else:
            data["cursor"] = n
            _clear_selection(data)
        data["preferred_col"] = None
        _ensure_cursor_visible(data, window_rect)
        return

    if event.key in (pygame.K_UP, pygame.K_DOWN):
        line, col, _ = _index_to_line_col(data["buffer"], data["cursor"])
        if data["preferred_col"] is None:
            data["preferred_col"] = col
        target_line = line - 1 if event.key == pygame.K_UP else line + 1
        n = _line_col_to_index(data["buffer"], target_line, data["preferred_col"])
        if shift:
            if data["sel_anchor"] is None:
                data["sel_anchor"] = data["cursor"]
            data["cursor"] = n
            data["sel_focus"] = n
        else:
            data["cursor"] = n
            _clear_selection(data)
        _ensure_cursor_visible(data, window_rect)
        return

    if event.key == pygame.K_HOME:
        if ctrl:
            n = 0
        else:
            line, _, starts = _index_to_line_col(data["buffer"], data["cursor"])
            n = starts[line]
        if shift:
            if data["sel_anchor"] is None:
                data["sel_anchor"] = data["cursor"]
            data["cursor"] = n
            data["sel_focus"] = n
        else:
            data["cursor"] = n
            _clear_selection(data)
        data["preferred_col"] = None
        _ensure_cursor_visible(data, window_rect)
        return

    if event.key == pygame.K_END:
        if ctrl:
            n = len(data["buffer"])
        else:
            line, _, starts = _index_to_line_col(data["buffer"], data["cursor"])
            if line + 1 < len(starts):
                n = starts[line + 1] - 1
            else:
                n = len(data["buffer"])
        if shift:
            if data["sel_anchor"] is None:
                data["sel_anchor"] = data["cursor"]
            data["cursor"] = n
            data["sel_focus"] = n
        else:
            data["cursor"] = n
            _clear_selection(data)
        data["preferred_col"] = None
        _ensure_cursor_visible(data, window_rect)
        return

    if event.key == pygame.K_BACKSPACE:
        if ctrl:
            _delete_word_left(data)
        else:
            if _selection_range(data):
                _push_undo(data)
                data["redo"].clear()
                _delete_selection(data)
            elif data["cursor"] > 0:
                _push_undo(data)
                data["redo"].clear()
                c = data["cursor"]
                data["buffer"] = data["buffer"][:c - 1] + data["buffer"][c:]
                data["cursor"] = c - 1
        data["preferred_col"] = None
        _ensure_cursor_visible(data, window_rect)
        return

    if event.key == pygame.K_DELETE:
        if ctrl:
            _delete_word_right(data)
        else:
            if _selection_range(data):
                _push_undo(data)
                data["redo"].clear()
                _delete_selection(data)
            elif data["cursor"] < len(data["buffer"]):
                _push_undo(data)
                data["redo"].clear()
                c = data["cursor"]
                data["buffer"] = data["buffer"][:c] + data["buffer"][c + 1:]
        data["preferred_col"] = None
        _ensure_cursor_visible(data, window_rect)
        return

    if event.key == pygame.K_RETURN:
        _insert_text(data, "\n")
        data["preferred_col"] = None
        _ensure_cursor_visible(data, window_rect)
        return

    if event.key == pygame.K_TAB:
        _insert_text(data, "    ")
        _ensure_cursor_visible(data, window_rect)
        return

    if event.unicode and event.unicode.isprintable() and not ctrl:
        _insert_text(data, event.unicode)
        data["preferred_col"] = None
        _ensure_cursor_visible(data, window_rect)


def draw_content(surface, rect, data, is_active):
    _ensure_state(data)
    font = pygame.font.SysFont("Consolas", 14)
    line_h = 18

    inner = pygame.Rect(rect.x + 5, rect.y + 36, rect.w - 10, rect.h - 41)
    pygame.draw.rect(surface, (252, 252, 252), inner)

    tx = inner.x + 5
    ty = inner.y + 4
    lines = data["buffer"].split("\n")

    first_line = max(0, data["scroll_y"] // line_h)
    visible_lines = max(1, inner.h // line_h + 2)
    last_line = min(len(lines), first_line + visible_lines)

    sel = _selection_range(data)
    if sel:
        s_idx, e_idx = sel
        s_line, s_col, _ = _index_to_line_col(data["buffer"], s_idx)
        e_line, e_col, _ = _index_to_line_col(data["buffer"], e_idx)
        for ln in range(max(first_line, s_line), min(last_line, e_line + 1)):
            line_text = lines[ln]
            if ln == s_line:
                c0 = s_col
            else:
                c0 = 0
            if ln == e_line:
                c1 = e_col
            else:
                c1 = len(line_text)
            x0 = tx + font.size(line_text[:c0])[0]
            x1 = tx + font.size(line_text[:c1])[0]
            y = ty + (ln * line_h) - data["scroll_y"]
            if x1 > x0:
                pygame.draw.rect(surface, (199, 224, 255), (x0, y, x1 - x0, line_h))

    for i in range(first_line, last_line):
        y = ty + (i * line_h) - data["scroll_y"]
        ts = font.render(lines[i], True, (30, 30, 30))
        surface.blit(ts, (tx, y))

    if is_active and (pygame.time.get_ticks() // 500) % 2 == 0:
        c_line, c_col, _ = _index_to_line_col(data["buffer"], data["cursor"])
        if first_line <= c_line < last_line:
            y = ty + (c_line * line_h) - data["scroll_y"]
            cx = tx + font.size(lines[c_line][:c_col])[0]
            pygame.draw.line(surface, (34, 40, 50), (cx, y + 1), (cx, y + line_h - 2), 2)



