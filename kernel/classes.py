import pygame

class ContextMenu:
    def __init__(self, x, y, options, target_app):
        self.rect = pygame.Rect(x, y, 150, len(options) * 30 + 10)
        self.options, self.target = options, target_app
        self.font = pygame.font.SysFont("Segoe UI", 14)

    def draw(self, surface, mx, my):
        pygame.draw.rect(surface, (255, 255, 255), self.rect, border_radius=5)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 1, border_radius=5)
        for i, opt in enumerate(self.options):
            r = pygame.Rect(self.rect.x + 5, self.rect.y + 5 + (i * 30), 140, 25)
            if r.collidepoint(mx, my): pygame.draw.rect(surface, (230, 230, 230), r, border_radius=3)
            surface.blit(self.font.render(opt, True, (50, 50, 50)), (r.x + 10, r.y + 3))

    def get_choice(self, mx, my):
        if not self.rect.collidepoint(mx, my): return None
        idx = (my - (self.rect.y + 5)) // 30
        return self.options[int(idx)] if 0 <= idx < len(self.options) else None

class AppWindow:
    def __init__(self, name, app_module, icon):
        self.name, self.module, self.icon = name, app_module, icon
        
        # Initialize app data from kebabapp metadata or from function
        if hasattr(self.module, 'init_data_dict'):
            self.app_data = dict(self.module.init_data_dict)
        elif hasattr(self.module, "init_data"):
            self.app_data = self.module.init_data()
        else:
            self.app_data = {}
        
        # Get config from kebabapp metadata or from module
        if hasattr(self.module, 'config'):
            dw, dh = self.module.config.get("width", 400), self.module.config.get("height", 300)
        else:
            dw, dh = 400, 300
        
        import random
        self.rect = pygame.Rect(100 + random.randint(0,100), 100 + random.randint(0,100), dw, dh)
        self.dragging = self.resizing = False
        self.offset_x = self.offset_y = 0
        self.is_fullscreen = False
        self.restore_rect = self.rect.copy()
        self.drag_restore_pending = False
        self.drag_start_x = 0
        self.drag_start_y = 0

    def toggle_fullscreen(self, max_w, max_h, taskbar_h=50):
        if not self.is_fullscreen:
            self.restore_rect = self.rect.copy()
            self.rect.x = 0
            self.rect.y = 0
            self.rect.w = max_w
            self.rect.h = max_h - taskbar_h
            self.is_fullscreen = True
        else:
            self.rect = self.restore_rect.copy()
            max_bottom = max_h - taskbar_h
            if self.rect.bottom > max_bottom:
                self.rect.h = max(120, max_bottom - self.rect.y)
            self.is_fullscreen = False

    def draw(self, surface, mx, my, is_active, close_img, fullscreen_img=None, windowed_img=None):
        frame_color = (250, 251, 253)
        border_color = (198, 206, 220)
        if not self.is_fullscreen:
            pygame.draw.rect(surface, frame_color, self.rect, border_radius=12)
            pygame.draw.rect(surface, border_color, self.rect, 1, border_radius=12)
        else:
            # Fullscreen should be edge-to-edge with square corners.
            pygame.draw.rect(surface, frame_color, self.rect)
            pygame.draw.rect(surface, border_color, self.rect, 1)

        # Clean title bar with subtle divider and active accent
        h_r = pygame.Rect(self.rect.x, self.rect.y, self.rect.w, 36)
        header_color = (247, 249, 252)
        if not self.is_fullscreen:
            pygame.draw.rect(surface, header_color, h_r, border_top_left_radius=12, border_top_right_radius=12)
        else:
            pygame.draw.rect(surface, header_color, h_r)
        pygame.draw.line(surface, (224, 229, 238), (self.rect.x + 1, self.rect.y + 35), (self.rect.right - 1, self.rect.y + 35), 1)
        if is_active:
            pygame.draw.rect(surface, (112, 154, 234), (self.rect.x + 12, self.rect.y + 4, 46, 3), border_radius=2)

        # Window title + icon (less heavy)
        title_x = self.rect.x + 12
        if self.icon:
            surface.blit(pygame.transform.scale(self.icon, (16, 16)), (self.rect.x + 10, self.rect.y + 10))
            title_x = self.rect.x + 32
        title_col = (52, 61, 74)
        t = pygame.font.SysFont("Segoe UI", 12, bold=False).render(self.name, True, title_col)
        surface.blit(t, (title_x, self.rect.y + 10))

        # Minimal close button
        self.close_r = pygame.Rect(self.rect.right - 36, self.rect.y + 6, 28, 24)
        self.fullscreen_r = pygame.Rect(self.rect.right - 68, self.rect.y + 6, 28, 24)

        fs_hover = self.fullscreen_r.collidepoint(mx, my)
        if fs_hover:
            pygame.draw.rect(surface, (228, 235, 246), self.fullscreen_r, border_radius=6)
        else:
            pygame.draw.rect(surface, (242, 245, 250), self.fullscreen_r, border_radius=6)

        fs_icon = windowed_img if self.is_fullscreen else fullscreen_img
        if fs_icon:
            surface.blit(fs_icon, (self.fullscreen_r.x + (self.fullscreen_r.w - fs_icon.get_width()) // 2, self.fullscreen_r.y + (self.fullscreen_r.h - fs_icon.get_height()) // 2))

        close_hover = self.close_r.collidepoint(mx, my)
        if close_hover:
            pygame.draw.rect(surface, (239, 112, 112), self.close_r, border_radius=6)
            x_col = (255, 255, 255)
        else:
            pygame.draw.rect(surface, (242, 245, 250), self.close_r, border_radius=6)
            x_col = (128, 137, 151)
        cx, cy = self.close_r.center
        pygame.draw.line(surface, x_col, (cx - 5, cy - 5), (cx + 5, cy + 5), 2)
        pygame.draw.line(surface, x_col, (cx + 5, cy - 5), (cx - 5, cy + 5), 2)

        self.resize_r = pygame.Rect(self.rect.right - 15, self.rect.bottom - 15, 15, 15)
        
        # Content Clipping
        clip_rect = pygame.Rect(self.rect.x + 2, self.rect.y + 36, self.rect.w - 4, self.rect.h - 38)
        self.content_rect = clip_rect.copy()
        surface.set_clip(clip_rect) 
        self.module.draw_content(surface, self.rect, self.app_data, is_active)
        surface.set_clip(None)
