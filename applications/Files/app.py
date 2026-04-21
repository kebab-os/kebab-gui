import pygame, os

def draw_content(screen, rect, data, is_active):
    inner = pygame.Rect(rect.x + 5, rect.y + 35, rect.w - 10, rect.h - 40)
    pygame.draw.rect(screen, (255, 255, 255), inner)
    f = pygame.font.SysFont("Segoe UI", 14)
    
    try: 
        files = os.listdir("storage/files")
    except: 
        files = []
    
    screen.blit(f.render("Explorer:", True, (0, 184, 148)), (rect.x + 15, rect.y + 45))
    
    for i, file in enumerate(files):
        screen.blit(f.render(f"> {file}", True, (50, 50, 50)), (rect.x + 15, rect.y + 70 + (i * 22)))
