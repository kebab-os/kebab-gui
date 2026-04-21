import pygame

def draw_content(surface, rect, data, is_active):
    inner = pygame.Rect(rect.x + 5, rect.y + 35, rect.w - 10, rect.h - 40)
    pygame.draw.rect(surface, (245, 245, 245), inner)
    
    disp = pygame.Rect(rect.x + 10, rect.y + 45, rect.w - 20, 40)
    pygame.draw.rect(surface, (255, 255, 255), disp, border_radius=5)
    f = pygame.font.SysFont("Consolas", 18)
    surface.blit(f.render(data["exp"] if data["exp"] else "0", True, (30,30,30)), (disp.x+5, disp.y+10))

    btns = ['7','8','9','/','4','5','6','*','1','2','3','-','C','0','=','+']
    bw, bh = (rect.w - 40)//4, (rect.h - 120)//4
    mx, my = pygame.mouse.get_pos()
    m_down = pygame.mouse.get_pressed()[0]

    for i, char in enumerate(btns):
        br = pygame.Rect(rect.x+10+(i%4*(bw+5)), rect.y+100+(i//4*(bh+5)), bw, bh)
        col = (200, 200, 200) if br.collidepoint(mx, my) else (220, 220, 220)
        
        if is_active and br.collidepoint(mx, my) and m_down:
            pygame.time.delay(120)
            if char == 'C': data["exp"] = ""
            elif char == '=':
                try: data["exp"] = str(eval(data["exp"].replace('x','*')))
                except: data["exp"] = "Error"
            else: data["exp"] += char
        
        pygame.draw.rect(surface, col, br, border_radius=4)
        surface.blit(pygame.font.SysFont("Arial", 14, True).render(char, True, (50, 50, 50)), (br.centerx-5, br.centery-10))
