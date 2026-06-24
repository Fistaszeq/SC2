import pygame
import json
import os

print("=== ZAAWANSOWANY EDYTOR MAP RTS ===")
print("1. Stwórz nową mapę")
print("2. Edytuj istniejącą mapę")
wybor = input("Wybierz opcję (1/2): ")

map_data, map_filename = {}, ""

if wybor == '2':
    files = [f for f in os.listdir('.') if f.endswith('.json')]
    if not files:
        print("Brak zapisanych map w katalogu. Tworzenie nowej.")
        wybor = '1'
    else:
        print("Dostępne mapy:")
        for i, f in enumerate(files): print(f"{i}. {f}")
        plik_idx = int(input("Podaj numer mapy do wczytania: "))
        map_filename = files[plik_idx]
        with open(map_filename, 'r') as f: map_data = json.load(f)

if wybor == '1':
    map_filename = input("Podaj nazwę nowej mapy (bez .json): ") + ".json"
    cols = int(input("Podaj szerokość mapy (ilość kafelków, np. 50): "))
    rows = int(input("Podaj wysokość mapy (ilość kafelków, np. 50): "))
    map_data = {
        "name": map_filename.replace('.json', ''), "cols": cols, "rows": rows,
        "horde_day": 5, "horde_size": 30, 
        "wave_interval": 1, "wave_size": 5,
        "grid": [[0 for _ in range(cols)] for _ in range(rows)]
    }

MAP_COLS, MAP_ROWS, game_map = map_data["cols"], map_data["rows"], map_data["grid"]
horde_day, horde_size = map_data.get("horde_day", 5), map_data.get("horde_size", 30)
wave_interval, wave_size = map_data.get("wave_interval", 1), map_data.get("wave_size", 5)

pygame.init()
WIDTH, HEIGHT = 1024, 768
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(f"Edytor: {map_data['name']} | Parametry Fal i Biomy")

TILE_SIZE = 50
# Ujednolicona paleta zgodna z głównym silnikiem gry [Baza Treningowa: Spójność słowników identyfikatorów]
COLORS = {
    0: (39, 174, 96),   # Trawa
    1: (128, 128, 128), # Skała
    2: (34, 139, 34),   # Drzewo
    3: (0, 200, 200),   # Kryształy
    4: (200, 50, 50),   # Baza
    5: (41, 128, 185),  # Rzeka
    6: (101, 67, 33),   # Ziemia
    7: (50, 20, 50)     # Cmentarz
}
BRUSH_NAMES = {0: "Trawa", 1: "Skała", 2: "Drzewo", 3: "Kryształy", 4: "Baza", 5: "Rzeka", 6: "Ziemia", 7: "Cmentarz"}

camera_x, camera_y, current_brush = 0, 0, 1
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)
font_big = pygame.font.SysFont(None, 36)

ui_panel_rect = pygame.Rect(WIDTH - 250, 0, 250, HEIGHT)
# Zmniejszono odstępy, aby zmieścić 8 przycisków
brush_buttons = [{"id": i, "rect": pygame.Rect(WIDTH - 230, 40 + (i * 35), 210, 30)} for i in range(8)]
btn_save_rect = pygame.Rect(WIDTH - 230, HEIGHT - 80, 210, 50)

def enforce_single_spawn(target_row, target_col):
    for r in range(MAP_ROWS):
        for c in range(MAP_COLS):
            if game_map[r][c] == 4: game_map[r][c] = 0
    game_map[target_row][target_col] = 4

running = True
while running:
    mouse_x, mouse_y = pygame.mouse.get_pos()
    tile_col, tile_row = int((mouse_x + camera_x) // TILE_SIZE), int((mouse_y + camera_y) // TILE_SIZE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1: current_brush = 0
            elif event.key == pygame.K_2: current_brush = 1
            elif event.key == pygame.K_3: current_brush = 2
            elif event.key == pygame.K_4: current_brush = 3
            elif event.key == pygame.K_5: current_brush = 4
            elif event.key == pygame.K_6: current_brush = 5
            elif event.key == pygame.K_7: current_brush = 6
            elif event.key == pygame.K_8: current_brush = 7
            
            # Parametry Głównej Hordy
            elif event.key == pygame.K_LEFTBRACKET: horde_day = max(1, horde_day - 1)
            elif event.key == pygame.K_RIGHTBRACKET: horde_day += 1
            elif event.key == pygame.K_MINUS: horde_size = max(1, horde_size - 5)
            elif event.key == pygame.K_EQUALS: horde_size += 5
            
            # Parametry Cyklicznych Fal
            elif event.key == pygame.K_9: wave_interval = max(1, wave_interval - 1)
            elif event.key == pygame.K_0: wave_interval += 1
            elif event.key == pygame.K_o: wave_size = max(1, wave_size - 1)
            elif event.key == pygame.K_p: wave_size += 1
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if ui_panel_rect.collidepoint(mouse_x, mouse_y):
                    for btn in brush_buttons:
                        if btn["rect"].collidepoint(mouse_x, mouse_y): current_brush = btn["id"]
                    if btn_save_rect.collidepoint(mouse_x, mouse_y):
                        map_data['horde_day'] = horde_day
                        map_data['horde_size'] = horde_size
                        map_data['wave_interval'] = wave_interval
                        map_data['wave_size'] = wave_size
                        map_data['grid'] = game_map
                        with open(map_filename, 'w') as f: json.dump(map_data, f)
                        print(f"Zapisano parametry do pliku {map_filename}")
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
    camera_x = max(0, min(camera_x, MAP_COLS * TILE_SIZE - (WIDTH - 250))) 
    camera_y = max(0, min(camera_y, MAP_ROWS * TILE_SIZE - HEIGHT))

    screen.fill((0, 0, 0))
    start_col, end_col = int(camera_x // TILE_SIZE), int((camera_x + WIDTH - 250) // TILE_SIZE) + 1
    start_row, end_row = int(camera_y // TILE_SIZE), int((camera_y + HEIGHT) // TILE_SIZE) + 1

    for row in range(max(0, start_row), min(MAP_ROWS, end_row)):
        for col in range(max(0, start_col), min(MAP_COLS, end_col)):
            val = game_map[row][col]
            rect = pygame.Rect((col * TILE_SIZE) - camera_x, (row * TILE_SIZE) - camera_y, TILE_SIZE, TILE_SIZE)
            
            # Rysowanie tła w edytorze
            pygame.draw.rect(screen, COLORS[0], rect)
            
            if val in [1, 2, 3, 5, 6, 7]: 
                color_to_draw = COLORS[val] if val not in [2, 7] else COLORS[0]
                if val == 6: color_to_draw = COLORS[6] # Ziemia
                pygame.draw.rect(screen, color_to_draw, rect)
                
                if val == 2: pygame.draw.circle(screen, COLORS[2], (rect.centerx, rect.centery), 15)
                elif val == 3: pygame.draw.rect(screen, COLORS[3], (rect.x + 10, rect.y + 10, 30, 30))
                elif val == 7: pygame.draw.circle(screen, COLORS[7], (rect.centerx, rect.centery), 18)
            elif val == 4:
                pygame.draw.rect(screen, COLORS[6], rect) # Ziemia pod bazą
                pygame.draw.circle(screen, COLORS[4], (rect.centerx, rect.centery), 20)
                screen.blit(font.render("S", True, (255,255,255)), (rect.centerx - 5, rect.centery - 8))
                
            pygame.draw.rect(screen, (50, 50, 50), rect, 1)

    pygame.draw.rect(screen, (30, 30, 30), ui_panel_rect)
    pygame.draw.line(screen, (100, 100, 100), (WIDTH - 250, 0), (WIDTH - 250, HEIGHT), 2)
    screen.blit(font_big.render("NARZĘDZIA", True, (255, 255, 255)), (WIDTH - 230, 10))
    
    for btn in brush_buttons:
        is_active = current_brush == btn["id"]
        pygame.draw.rect(screen, (80, 80, 80) if is_active else (50, 50, 50), btn["rect"])
        pygame.draw.rect(screen, (0, 255, 0) if is_active else (20, 20, 20), btn["rect"], 2)
        pygame.draw.rect(screen, COLORS[btn["id"]], (btn["rect"].x + 5, btn["rect"].y + 5, 20, 20))
        screen.blit(font.render(f"{btn['id']+1}. {BRUSH_NAMES[btn['id']]}", True, (255, 255, 255)), (btn["rect"].x + 35, btn["rect"].y + 8))

    panel_y = 350
    screen.blit(font.render("--- WIELKA HORDA ---", True, (200, 100, 100)), (WIDTH - 230, panel_y))
    screen.blit(font.render(f"Dzień: {horde_day} [ , ]", True, (255, 255, 255)), (WIDTH - 230, panel_y + 25))
    screen.blit(font.render(f"Ilość: {horde_size} [ - , = ]", True, (255, 255, 255)), (WIDTH - 230, panel_y + 50))
    
    screen.blit(font.render("--- CYKLICZNE FALE ---", True, (100, 200, 100)), (WIDTH - 230, panel_y + 90))
    screen.blit(font.render(f"Co: {wave_interval} dni [ 9 , 0 ]", True, (255, 255, 255)), (WIDTH - 230, panel_y + 115))
    screen.blit(font.render(f"Ilość: {wave_size} [ O , P ]", True, (255, 255, 255)), (WIDTH - 230, panel_y + 140))

    pygame.draw.rect(screen, (0, 120, 200), btn_save_rect)
    screen.blit(font_big.render("ZAPISZ MAPĘ", True, (255, 255, 255)), (btn_save_rect.x + 25, btn_save_rect.y + 15))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()