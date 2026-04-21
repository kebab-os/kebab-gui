import os
import xml.etree.ElementTree as ET

import pygame


HEADING_SIZES = {
    "h1": 34,
    "h2": 28,
    "h3": 24,
    "h4": 20,
    "h5": 16,
    "h6": 14,
}


def _parse_style(style_str):
    styles = {}
    if not style_str:
        return styles
    for item in style_str.split(";"):
        if ":" in item:
            key, val = item.split(":", 1)
            styles[key.strip().lower()] = val.strip()
    return styles


def _parse_int(value, default=0):
    try:
        if isinstance(value, (int, float)):
            return int(value)
        value = str(value).strip()
        if value.endswith("px"):
            value = value[:-2]
        if value.endswith("%"):
            return default
        return int(float(value))
    except Exception:
        return default


def _parse_color(value, default=None):
    if value is None:
        return default
    value = str(value).strip()
    if not value:
        return default
    if value.startswith("#") and len(value) in (4, 7):
        if len(value) == 4:
            r = int(value[1] * 2, 16)
            g = int(value[2] * 2, 16)
            b = int(value[3] * 2, 16)
            return (r, g, b)
        r = int(value[1:3], 16)
        g = int(value[3:5], 16)
        b = int(value[5:7], 16)
        return (r, g, b)
    try:
        parts = [int(part.strip()) for part in value.split(",")[:3]]
        if len(parts) == 3:
            return tuple(max(0, min(255, part)) for part in parts)
    except Exception:
        pass
    return default


def _wrap_text(font, text, max_width):
    if not text:
        return [""]

    lines = []
    for source_line in text.split("\n"):
        words = source_line.split()
        if not words:
            lines.append("")
            continue

        current = words[0]
        for word in words[1:]:
            trial = current + " " + word
            if font.size(trial)[0] <= max_width:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)

    return lines or [text]


def _load_markup(markup_str):
    try:
        root = ET.fromstring(markup_str)
    except Exception:
        return None
    content = root.find("content")
    return content if content is not None else root


def create_static_draw_content(markup_str, app_dir):
    root = _load_markup(markup_str)

    def draw_content(surface, rect, data, is_active):
        if root is None:
            return

        font_cache = {}

        def get_font(size, bold=False, italic=False, family="Segoe UI"):
            key = (size, bold, italic, family)
            if key not in font_cache:
                font_cache[key] = pygame.font.SysFont(family, size, bold=bold, italic=italic)
            return font_cache[key]

        def draw_text_block(text, x, y, width, size=16, color=(35, 42, 56), bold=False, italic=False, align="left"):
            font = get_font(size, bold=bold, italic=italic)
            lines = _wrap_text(font, text, max(10, width))
            line_h = max(size + 6, font.get_height() + 2)
            start_y = y
            for line in lines:
                surf = font.render(line, True, color)
                if align == "center":
                    draw_x = x + (width - surf.get_width()) // 2
                elif align == "right":
                    draw_x = x + width - surf.get_width()
                else:
                    draw_x = x
                surface.blit(surf, (draw_x, y))
                y += line_h
            return y - start_y

        def render_node(node, x, y, width):
            tag = (node.tag or "").lower()
            styles = _parse_style(node.attrib.get("style", ""))
            margin = _parse_int(styles.get("margin", 0), 0)
            padding = _parse_int(styles.get("padding", 0), 0)
            text_color = _parse_color(styles.get("color"), (35, 42, 56))
            bg_color = _parse_color(styles.get("bg") or styles.get("background") or styles.get("background-color"))
            border_color = _parse_color(styles.get("border_color") or styles.get("border-color"), (0, 0, 0))
            border_size = _parse_int(styles.get("border"), 0)
            radius = _parse_int(styles.get("radius"), 0)
            align = styles.get("align", styles.get("text-align", "left")).lower()
            size_override = _parse_int(styles.get("font-size"), 0)
            family = styles.get("font", "Segoe UI")
            bold = styles.get("bold", "false").lower() in ("1", "true", "yes")
            italic = styles.get("italic", "false").lower() in ("1", "true", "yes")

            x += margin
            y += margin
            width = max(10, width - (margin * 2))

            text = (node.text or "").strip()
            if tag == "br":
                return 14 + margin * 2

            if tag in HEADING_SIZES:
                size = size_override or HEADING_SIZES[tag]
                h = draw_text_block(text, x, y, width, size=size, color=text_color, bold=True, align=align)
                return h + margin

            if tag in ("p", "span", "label"):
                size = size_override or 16
                h = draw_text_block(text, x, y, width, size=size, color=text_color, bold=bold, italic=italic, align=align)
                return h + margin

            if tag == "hr":
                line_y = y + 8
                pygame.draw.line(surface, border_color or (208, 214, 226), (x, line_y), (x + width, line_y), 1)
                return 16 + margin

            if tag == "button":
                size = size_override or 16
                font = get_font(size, bold=bold or True, family=family)
                txt = text
                text_surf = font.render(txt, True, text_color)
                box_w = _parse_int(styles.get("width"), max(110, text_surf.get_width() + 28))
                box_h = _parse_int(styles.get("height"), max(34, text_surf.get_height() + 18))
                box = pygame.Rect(x, y, min(box_w, width), box_h)
                pygame.draw.rect(surface, bg_color or (242, 245, 250), box, border_radius=max(0, radius or 8))
                if border_size:
                    pygame.draw.rect(surface, border_color, box, border_size, border_radius=max(0, radius or 8))
                surface.blit(text_surf, (box.x + (box.w - text_surf.get_width()) // 2, box.y + (box.h - text_surf.get_height()) // 2))
                return box_h + margin

            if tag == "img":
                src = node.attrib.get("src", "").strip()
                img_path = os.path.join(app_dir, src) if src and not os.path.isabs(src) else src
                if img_path and os.path.exists(img_path):
                    try:
                        img = pygame.image.load(img_path)
                        target_w = _parse_int(styles.get("width"), img.get_width())
                        target_h = _parse_int(styles.get("height"), img.get_height())
                        img = pygame.transform.smoothscale(img.convert_alpha(), (max(1, target_w), max(1, target_h)))
                        surface.blit(img, (x, y))
                        return img.get_height() + margin
                    except Exception:
                        pass
                placeholder = get_font(14).render("[image]", True, text_color)
                surface.blit(placeholder, (x, y))
                return placeholder.get_height() + margin

            if tag in ("ul", "ol"):
                total_h = 0
                for idx, child in enumerate(node):
                    if (child.tag or "").lower() != "li":
                        continue
                    bullet = "•" if tag == "ul" else f"{idx + 1}."
                    bullet_font = get_font(size_override or 16, bold=True, family=family)
                    bullet_surf = bullet_font.render(bullet, True, text_color)
                    surface.blit(bullet_surf, (x, y + total_h))
                    child_text = (child.text or "").strip()
                    child_h = draw_text_block(child_text, x + 22, y + total_h, max(10, width - 22), size=size_override or 16, color=text_color, align=align)
                    total_h += max(child_h, bullet_surf.get_height()) + 6
                return total_h + margin

            # Generic container / unknown tag.
            child_x = x + padding
            child_y = y + padding
            child_w = max(10, width - (padding * 2))
            total_h = 0
            if bg_color is not None or border_size:
                min_h = _parse_int(styles.get("height"), 0)
                box_w = _parse_int(styles.get("width"), width)
                box_h = max(min_h, 0)
                box = pygame.Rect(x, y, min(box_w, width), max(box_h, 18))
                if bg_color is not None:
                    pygame.draw.rect(surface, bg_color, box, border_radius=max(0, radius))
                if border_size:
                    pygame.draw.rect(surface, border_color, box, border_size, border_radius=max(0, radius))
                child_x = box.x + padding
                child_y = box.y + padding
                child_w = max(10, box.w - padding * 2)

            if text:
                text_h = draw_text_block(text, child_x, child_y, child_w, size=size_override or 16, color=text_color, bold=bold, align=align)
                total_h += text_h + 4
                child_y += text_h + 4

            for child in node:
                total_h += render_node(child, child_x, child_y + total_h, child_w)

            if total_h == 0:
                total_h = _parse_int(styles.get("height"), 20)

            return total_h + (margin * 2)

        y = rect.y + 10
        x = rect.x + 10
        width = rect.w - 20
        for child in root:
            y += render_node(child, x, y, width)
            y += 4

    return draw_content
