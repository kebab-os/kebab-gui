import kebab_graphics as pygame
import os


def _get_files_dir():
    user_dir = os.environ.get("KEBAB_USER_FILES_DIR", "").strip()
    if user_dir:
        os.makedirs(user_dir, exist_ok=True)
        return user_dir

    fallback = "storage/files"
    os.makedirs(fallback, exist_ok=True)
    return fallback


def draw_content(screen, rect, data, is_active):
    inner = pygame.Rect(rect.x + 5, rect.y + 35, rect.w - 10, rect.h - 40)
    pygame.draw.rect(screen, (255, 255, 255), inner)
    f = pygame.font.SysFont("Segoe UI", 14)
    
    try:
        files = os.listdir(_get_files_dir())
    except: 
        files = []
    
    screen.blit(f.render("Explorer:", True, (0, 184, 148)), (rect.x + 15, rect.y + 45))
    
    for i, file in enumerate(files):
        screen.blit(f.render(f"> {file}", True, (50, 50, 50)), (rect.x + 15, rect.y + 70 + (i * 22)))
