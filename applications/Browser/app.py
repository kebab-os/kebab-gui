import kebab_graphics as pygame
import requests
import os
from html2image import Html2Image

hti = Html2Image(custom_flags=['--no-sandbox', '--disable-gpu'])

def handle_input(event, data):
    # --- MOUSE CLICK (For Clear Button) ---
    if event.type == pygame.MOUSEBUTTONDOWN:
        # We need to calculate the clear button position relative to the app window
        # Note: This requires knowing the app's current 'rect' from draw_content
        pass 

    if event.type == pygame.KEYDOWN:
        ctrl_pressed = pygame.key.get_mods() & pygame.KMOD_CTRL
        if event.key == pygame.K_v and ctrl_pressed:
            pasted_bytes = pygame.scrap.get(pygame.SCRAP_TEXT)
            if pasted_bytes:
                data["input"] += pasted_bytes.decode('utf-8').strip('\x00')
        
        elif event.key == pygame.K_RETURN:
            data["loading"] = True
            data["error"] = ""
            try:
                hti.screenshot(url=data["input"], save_as='web_temp.png')
                raw_img = pygame.image.load('web_temp.png').convert_alpha()
                w, h = raw_img.get_size()
                scale = (600 - 20) / w
                data["page_surf"] = pygame.transform.smoothscale(raw_img, (int(w * scale), int(h * scale)))
                data["scroll_y"] = 0
            except Exception as e: data["error"] = str(e)
            data["loading"] = False
        
        elif event.key == pygame.K_BACKSPACE:
            data["input"] = data["input"][:-1]
        elif event.unicode.isprintable():
            data["input"] += event.unicode

    elif event.type == pygame.MOUSEWHEEL:
        data["scroll_y"] = max(0, data["scroll_y"] - event.y * 35)

def draw_content(screen, rect, data, is_active):
    f_ui = pygame.font.SysFont("Segoe UI", 13)
    inner = pygame.Rect(rect.x + 2, rect.y + 30, rect.w - 4, rect.h - 32)
    pygame.draw.rect(screen, (255, 255, 255), inner)

    # --- Address Bar ---
    bar = pygame.Rect(rect.x + 10, rect.y + 40, rect.w - 20, 28)
    pygame.draw.rect(screen, (245, 245, 245), bar, border_radius=5)
    pygame.draw.rect(screen, (200, 200, 200), bar, 1, border_radius=5)
    
    # --- Clear Button (The "X") ---
    clear_rect = pygame.Rect(bar.right - 25, bar.y + 4, 20, 20)
    mx, my = pygame.mouse.get_pos()
    
    # Logic for clicking the clear button
    if clear_rect.collidepoint(mx, my) and pygame.mouse.get_pressed()[0]:
        data["input"] = ""

    # Draw the Clear Button
    if clear_rect.collidepoint(mx, my):
        pygame.draw.rect(screen, (230, 230, 230), clear_rect, border_radius=10)
    screen.blit(f_ui.render("×", True, (150, 150, 150)), (clear_rect.x + 5, clear_rect.y - 2))

    # Text Input
    cursor = "|" if is_active and (pygame.time.get_ticks() // 500) % 2 == 0 else ""
    # Clip text so it doesn't overlap the "X"
    text_clip = pygame.Rect(bar.x + 5, bar.y, bar.w - 30, bar.h)
    old_clip = screen.get_clip()
    screen.set_clip(text_clip)
    screen.blit(f_ui.render(data["input"] + cursor, True, (60, 60, 60)), (bar.x + 10, bar.y + 4))
    screen.set_clip(old_clip)

    # --- Web Viewport ---
    view_rect = pygame.Rect(rect.x + 5, rect.y + 75, rect.w - 10, rect.h - 80)
    screen.set_clip(view_rect)
    if data["loading"]:
        screen.blit(f_ui.render("Rendering...", True, (100, 100, 100)), (view_rect.x + 10, view_rect.y + 10))
    elif data["page_surf"]:
        screen.blit(data["page_surf"], (view_rect.x, view_rect.y - data["scroll_y"]))
    screen.set_clip(old_clip)

