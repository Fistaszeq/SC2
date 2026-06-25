import pygame
import json
import os

pygame.init()
WIDTH, HEIGHT = 1024, 768
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Edytor Map RTS")

font_main = pygame.font.SysFont(None, 28)
font_title = pygame.font.SysFont(None, 64, bold=True)
font_small = pygame.font.SysFont(None, 22)

# --- MENU GŁÓWNE EDYTORA ---
def show_editor_menu():
    clock = pygame.time.Clock()
    files = [f for f in os.listdir('.') if f.endswith('.json')]
    selected_idx = -1 
    
    while True:
        screen.fill((20, 20, 20))
        mouse_x, mouse_y = pygame.mouse.get_pos()
        clicked = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: clicked = True
            
        screen.blit(font_title.render("EDYTOR MAP", True, (0, 255, 150)), (WIDTH//2 - 160, 50))
        
        btn_new = pygame.Rect(WIDTH//2 - 200, 150, 400, 50)
        pygame.draw.rect(screen, (50, 50, 50), btn_new)
        if selected_idx == -1: pygame.draw.rect(screen, (0, 255, 0), btn_new, 3)
        screen.blit(font_main.render("Nowa Mapa (Pusta 50x50)", True, (255, 255, 255)), (btn_new.x + 40, btn_new.y + 15))
        if btn_new.collidepoint(mouse_x, mouse_y) and clicked: selected_idx = -1
        
        for i, f in enumerate(files[:8]): 
            f_rect = pygame.Rect(WIDTH//2 - 200, 220 + i*55, 400, 45)
            pygame.draw.rect(screen, (40, 40, 40), f_rect)
            if selected_idx == i: pygame.draw.rect(screen, (0, 255, 0), f_rect, 3)
            screen.blit(font_main.render(f"Edytuj: {f}", True, (255, 255, 255)), (f_rect.x + 40, f_rect.y + 12))
            if f_rect.collidepoint(mouse_x, mouse_y) and clicked: selected_idx = i
            
        btn_start = pygame.Rect(WIDTH//2 - 100, HEIGHT - 100, 200, 60)
        pygame.draw.rect(screen, (0, 120, 255), btn_start)
        screen.blit(font_main.render("URUCHOM EDYTOR", True, (255, 255, 255)), (btn_start.x + 15, btn_start.y + 20))
        
        if btn_start.collidepoint(mouse_x, mouse_y) and clicked:
            if selected_idx == -1:
                return {
                    "name": "nowa_mapa", "cols": 50, "rows": 50,
                    "day_length_frames": 14000,
                    "horde_day": 5, "horde_size": 30, 
                    "wave_interval_hours": 24, "wave_size": 5,
                    "grid": [[0 for _ in range(50)] for _ in range(50)]
                }, "nowa_mapa.json"
            else:
                with open(files[selected_idx], 'r') as f:
                    return json.load(f), files[selected_idx]
                
        pygame.display.flip()
        clock.tick(60)

map_data, map_filename = show_editor_menu()

MAP_COLS, MAP_ROWS, game_map = map_data["cols"], map_data["rows"], map_data["grid"]
day_length_frames = map_data.get("day_length_frames", 14000)
horde_day, horde_size = map_data.get("horde_day", 5), map_data.get("horde_size", 30)
wave_interval_hours, wave_size = map_data.get("wave_interval_hours", 24), map_data.get("wave_size", 5)

pygame.display.set_caption(f"Edytor: {map_filename}")

TILE_SIZE = 50
COLORS = {
    0: (39, 174, 96),   1: (128, 128, 128), 2: (34, 139, 34),   3: (0, 200, 200),
    4: (200, 50, 50),   5: (41, 128, 185),  6: (101, 67, 33),   7: (50, 20, 50)
}
BRUSH_NAMES = {0: "Trawa", 1: "Skała", 2: "Drzewo", 3: "Kryształy", 4: "Baza", 5: "Rzeka", 6: "Ziemia", 7: "Cmentarz"}

camera_x, camera_y, current_brush = 0, 0, 1
clock = pygame.time.Clock()

ui_panel_rect = pygame.Rect(WIDTH - 320, 0, 320, HEIGHT)
brush_buttons = [{"id": i, "rect": pygame.Rect(WIDTH - 300, 40 + (i * 35), 280, 30)} for i in range(8)]
btn_save_rect = pygame.Rect(WIDTH - 300, HEIGHT - 80, 280, 50)

def enforce_single_spawn(target_row, target_col):
    for r in range(MAP_ROWS):
        for c in range(MAP_COLS):
            if game_map[r][c] == 4: game_map[r][c] = 0
    game_map[target_row][target_col] = 4

# Pola interfejsu numerycznego
params_ui = [
    {"label": "Długość Dnia (klatki)", "var": "day", "min": 1000, "max": 60000, "step": 500},
    {"label": "Wielka Horda: Dzień", "var": "h_day", "min": 1, "max": 100, "step": 1},
    {"label": "Wielka Horda: Ilość", "var": "h_size", "min": 1, "max": 500, "step": 5},
    {"label": "Cykliczne: Co (godzin)", "var": "w_int", "min": 1, "max": 72, "step": 1},
    {"label": "Cykliczne: Ilość", "var": "w_size", "min": 1, "max": 100, "step": 1}
]

for i, p in enumerate(params_ui):
    y_pos = 350 + (i * 60)
    p["rect_minus"] = pygame.Rect(WIDTH - 300, y_pos + 25, 40, 30)
    p["rect_plus"] = pygame.Rect(WIDTH - 80, y_pos + 25, 40, 30)

running = True
while running:
    mouse_x, mouse_y = pygame.mouse.get_pos()
    tile_col, tile_row = int((mouse_x + camera_x) // TILE_SIZE), int((mouse_y + camera_y) // TILE_SIZE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if ui_panel_rect.collidepoint(mouse_x, mouse_y):
                    for btn in brush_buttons:
                        if btn["rect"].collidepoint(mouse_x, mouse_y): current_brush = btn["id"]
                    
                    if btn_save_rect.collidepoint(mouse_x, mouse_y):
                        map_data['day_length_frames'] = day_length_frames
                        map_data['horde_day'] = horde_day
                        map_data['horde_size'] = horde_size
                        map_data['wave_interval_hours'] = wave_interval_hours
                        map_data['wave_size'] = wave_size
                        map_data['grid'] = game_map
                        with open(map_filename, 'w') as f: json.dump(map_data, f)
                        print(f"Zapisano parametry do pliku {map_filename}")

                    for p in params_ui:
                        if p["rect_minus"].collidepoint(mouse_x, mouse_y):
                            if p["var"] == "day": day_length_frames = max(p["min"], day_length_frames - p["step"])
                            elif p["var"] == "h_day": horde_day = max(p["min"], horde_day - p["step"])
                            elif p["var"] == "h_size": horde_size = max(p["min"], horde_size - p["step"])
                            elif p["var"] == "w_int": wave_interval_hours = max(p["min"], wave_interval_hours - p["step"])
                            elif p["var"] == "w_size": wave_size = max(p["min"], wave_size - p["step"])
                        elif p["rect_plus"].collidepoint(mouse_x, mouse_y):
                            if p["var"] == "day": day_length_frames = min(p["max"], day_length_frames + p["step"])
                            elif p["var"] == "h_day": horde_day = min(p["max"], horde_day + p["step"])
                            elif p["var"] == "h_size": horde_size = min(p["max"], horde_size + p["step"])
                            elif p["var"] == "w_int": wave_interval_hours = min(p["max"], wave_interval_hours + p["step"])
                            elif p["var"] == "w_size": wave_size = min(p["max"], wave_size + p["step"])
                            
                elif 0 <= tile_row < MAP_ROWS and 0 <= tile_col < MAP_COLS:
                    if current_brush == 4: enforce_single_spawn(tile_row, tile_col)
                    else: game_map[tile_row][tile_col] = current_brush

        elif event.type == pygame.MOUSEMOTION:
            if pygame.mouse.get_pressed()[0] and not ui_panel_rect.collidepoint(mouse_x, mouse_y):
                if 0 <= tile_row < MAP_ROWS and 0 <= tile_col < MAP_COLS:
                    if current_brush == 4: enforce_single_spawn(tile_row, tile_col)
                    else: game_map[tile_row][tile_col] = current_brush

    kb = pygame.key.get_pressed()
    if kb[pygame.K_LEFT] or kb[pygame.K_a]: camera_x -= 20
    if kb[pygame.K_RIGHT] or kb[pygame.K_d]: camera_x += 20
    if kb[pygame.K_UP] or kb[pygame.K_w]: camera_y -= 20
    if kb[pygame.K_DOWN] or kb[pygame.K_s]: camera_y += 20
    camera_x = max(0, min(camera_x, MAP_COLS * TILE_SIZE - (WIDTH - 320))) 
    camera_y = max(0, min(camera_y, MAP_ROWS * TILE_SIZE - HEIGHT))

    screen.fill((0, 0, 0))
    start_col, end_col = int(camera_x // TILE_SIZE), int((camera_x + WIDTH - 320) // TILE_SIZE) + 1
    start_row, end_row = int(camera_y // TILE_SIZE), int((camera_y + HEIGHT) // TILE_SIZE) + 1

    for row in range(max(0, start_row), min(MAP_ROWS, end_row)):
        for col in range(max(0, start_col), min(MAP_COLS, end_col)):
            val = game_map[row][col]
            rect = pygame.Rect((col * TILE_SIZE) - camera_x, (row * TILE_SIZE) - camera_y, TILE_SIZE, TILE_SIZE)
            
            pygame.draw.rect(screen, COLORS[0], rect)
            if val in [1, 2, 3, 5, 6, 7]: 
                color_to_draw = COLORS[val] if val not in [2, 7] else COLORS[0]
                if val == 6: color_to_draw = COLORS[6] 
                pygame.draw.rect(screen, color_to_draw, rect)
                
                if val == 2: pygame.draw.circle(screen, COLORS[2], (rect.centerx, rect.centery), 15)
                elif val == 3: pygame.draw.rect(screen, COLORS[3], (rect.x + 10, rect.y + 10, 30, 30))
                elif val == 7: pygame.draw.circle(screen, COLORS[7], (rect.centerx, rect.centery), 18)
            elif val == 4:
                pygame.draw.rect(screen, COLORS[6], rect)
                pygame.draw.circle(screen, COLORS[4], (rect.centerx, rect.centery), 20)
                screen.blit(font_main.render("S", True, (255,255,255)), (rect.centerx - 5, rect.centery - 8))
                
            pygame.draw.rect(screen, (50, 50, 50), rect, 1)

    pygame.draw.rect(screen, (30, 30, 30), ui_panel_rect)
    pygame.draw.line(screen, (100, 100, 100), (WIDTH - 320, 0), (WIDTH - 320, HEIGHT), 2)
    screen.blit(font_title.render("NARZĘDZIA", True, (255, 255, 255)), (WIDTH - 300, 10))
    
    for btn in brush_buttons:
        is_active = current_brush == btn["id"]
        pygame.draw.rect(screen, (80, 80, 80) if is_active else (50, 50, 50), btn["rect"])
        pygame.draw.rect(screen, (0, 255, 0) if is_active else (20, 20, 20), btn["rect"], 2)
        pygame.draw.rect(screen, COLORS[btn["id"]], (btn["rect"].x + 5, btn["rect"].y + 5, 20, 20))
        screen.blit(font_main.render(f"{btn['id']+1}. {BRUSH_NAMES[btn['id']]}", True, (255, 255, 255)), (btn["rect"].x + 35, btn["rect"].y + 6))

    for i, p in enumerate(params_ui):
        y_pos = 350 + (i * 60)
        screen.blit(font_small.render(p["label"], True, (150, 200, 255)), (WIDTH - 300, y_pos))
        
        pygame.draw.rect(screen, (80, 50, 50), p["rect_minus"])
        screen.blit(font_main.render("-", True, (255, 255, 255)), (p["rect_minus"].x + 15, p["rect_minus"].y + 6))
        
        pygame.draw.rect(screen, (50, 80, 50), p["rect_plus"])
        screen.blit(font_main.render("+", True, (255, 255, 255)), (p["rect_plus"].x + 12, p["rect_plus"].y + 6))
        
        val_str = ""
        if p["var"] == "day": val_str = str(day_length_frames)
        elif p["var"] == "h_day": val_str = str(horde_day)
        elif p["var"] == "h_size": val_str = str(horde_size)
        elif p["var"] == "w_int": val_str = f"{wave_interval_hours}h"
        elif p["var"] == "w_size": val_str = str(wave_size)
        
        val_surf = font_main.render(val_str, True, (255, 255, 255))
        screen.blit(val_surf, (WIDTH - 190 + (50 - val_surf.get_width()//2), y_pos + 30))

    pygame.draw.rect(screen, (0, 120, 200), btn_save_rect)
    screen.blit(font_title.render("ZAPISZ", True, (255, 255, 255)), (btn_save_rect.x + 45, btn_save_rect.y + 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()