import pygame, math, random, json, os
from config import *
pygame.init()

WIDTH, HEIGHT = 1024, 768
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("RTS - Prawdziwa Mgła Wojny, Nowe Wieżyczki i UI SC2")

from entities import *

font_main = pygame.font.SysFont(None, 24)
font_small = pygame.font.SysFont(None, 18)
font_bold = pygame.font.SysFont(None, 24, bold=True)
font_info_title = pygame.font.SysFont(None, 28, bold=True)
font_title = pygame.font.SysFont(None, 64, bold=True)

global_message, global_message_timer = "", 0
def show_message(text):
    global global_message, global_message_timer
    global_message = text; global_message_timer = 120 

def show_main_menu():
    clock = pygame.time.Clock()
    files = [f for f in os.listdir('.') if f.endswith('.json')]
    selected_idx = -1 
    running_menu = True
    while running_menu:
        screen.fill(BLACK)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        clicked = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: clicked = True
        
        screen.blit(font_title.render("MÓJ STARCRAFT", True, YELLOW), (WIDTH//2 - 200, 80))
        rnd_rect = pygame.Rect(WIDTH//2 - 200, 220, 400, 50)
        pygame.draw.rect(screen, DARK_GRAY, rnd_rect)
        if selected_idx == -1: pygame.draw.rect(screen, GREEN, rnd_rect, 3)
        rnd_txt = font_main.render("Generuj Proceduralnie (Domyślna)", True, WHITE)
        screen.blit(rnd_txt, (rnd_rect.x + 40, rnd_rect.y + 15))
        if rnd_rect.collidepoint(mouse_x, mouse_y) and clicked: selected_idx = -1

        for i, f in enumerate(files[:6]): 
            f_rect = pygame.Rect(WIDTH//2 - 200, 290 + i*60, 400, 50)
            pygame.draw.rect(screen, DARK_GRAY, f_rect)
            if selected_idx == i: pygame.draw.rect(screen, GREEN, f_rect, 3)
            f_txt = font_main.render(f"Wczytaj: {f}", True, WHITE)
            screen.blit(f_txt, (f_rect.x + 40, f_rect.y + 15))
            if f_rect.collidepoint(mouse_x, mouse_y) and clicked: selected_idx = i

        start_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT - 150, 200, 60)
        pygame.draw.rect(screen, BLUE, start_rect)
        start_txt = font_bold.render("GRAJ", True, WHITE)
        screen.blit(start_txt, (start_rect.x + 65, start_rect.y + 20))
        if start_rect.collidepoint(mouse_x, mouse_y) and clicked: return None if selected_idx == -1 else files[selected_idx]

        pygame.display.flip(); clock.tick(60)

while True:
    selected_map_file = show_main_menu()
    
    MAP_COLS, MAP_ROWS = 50, 50
    WORLD_WIDTH, WORLD_HEIGHT = MAP_COLS * TILE_SIZE, MAP_ROWS * TILE_SIZE
    game_map, trees_data, crystals_data, cemetery_data = [], [], [], []
    base_spawn_col, base_spawn_row = 5, 5 
    
    day_length_frames = 14000
    horde_day, horde_size = 5, 30
    wave_interval_hours, wave_size = 24, 5
    last_wave_spawn_hour_global = -1
    
    def generate_cool_tactical_map():
        grid = [[0 for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]
        river_c = 25
        for r in range(MAP_ROWS):
            for w in range(-2, 3):
                if 0 <= river_c + w < MAP_COLS: grid[r][river_c + w] = 5
            if random.random() < 0.4: river_c += random.choice([-1, 1])
        for r in range(MAP_ROWS):
            for c in range(MAP_COLS):
                if grid[r][c] == 5: continue 
                if (r < 3 or r > MAP_ROWS-4 or c < 3 or c > MAP_COLS-4) and random.random() < 0.3: grid[r][c] = 1
                if c == 35 and not (12 < r < 18 or 32 < r < 38): grid[r][c] = 1
        for r in range(2, 12):
            for c in range(2, 12):
                if grid[r][c] not in [1, 5]: grid[r][c] = 6
        return grid
    
    if selected_map_file and os.path.exists(selected_map_file):
        with open(selected_map_file, 'r') as f: map_data = json.load(f)
        MAP_COLS, MAP_ROWS = map_data["cols"], map_data["rows"]
        WORLD_WIDTH, WORLD_HEIGHT = MAP_COLS * TILE_SIZE, MAP_ROWS * TILE_SIZE
        
        day_length_frames = map_data.get("day_length_frames", 14000)
        horde_day, horde_size = map_data.get("horde_day", 5), map_data.get("horde_size", 30)
        
        if "wave_interval_hours" in map_data:
            wave_interval_hours = map_data["wave_interval_hours"]
        else:
            wave_interval_hours = map_data.get("wave_interval", 1) * 24
            
        wave_size = map_data.get("wave_size", 5)
        game_map = map_data["grid"]
        
        for r in range(MAP_ROWS):
            for c in range(MAP_COLS):
                val = game_map[r][c]
                rx, ry = c * TILE_SIZE + TILE_SIZE//2, r * TILE_SIZE + TILE_SIZE//2
                if val == 2: trees_data.append((rx, ry)); game_map[r][c] = 0 
                elif val == 3: crystals_data.append((rx, ry)); game_map[r][c] = 0 
                elif val == 4: base_spawn_col, base_spawn_row = c, r; game_map[r][c] = 6 
                elif val == 7: cemetery_data.append((c, r)); game_map[r][c] = 6 
    else:
        game_map = generate_cool_tactical_map()
        for _ in range(15): trees_data.append((random.randint(100, 450), random.randint(450, 550)))
        for _ in range(8): crystals_data.append((random.randint(450, 550), random.randint(100, 400)))
        for _ in range(20): trees_data.append((random.randint(1300, 1600), random.randint(600, 1200)))
        for _ in range(12): crystals_data.append((random.randint(1400, 1700), random.randint(1300, 1600)))
        cemetery_data.extend([(46, 4), (46, 44), (4, 44)])
    
    def is_obstacle(x, y):
        col, row = int(x // TILE_SIZE), int(y // TILE_SIZE)
        if 0 <= row < MAP_ROWS and 0 <= col < MAP_COLS: return game_map[row][col] == 1
        return True
    
    def get_speed_mod(x, y):
        col, row = int(x // TILE_SIZE), int(y // TILE_SIZE)
        if 0 <= row < MAP_ROWS and 0 <= col < MAP_COLS:
            if game_map[row][col] == 5: return 0.5 
        return 1.0
    
    def get_zombie_spawn_point(buildings_list, max_w, max_h):
        bases = [b for b in buildings_list if b.b_type == 'base' and b.is_built]
        for _ in range(25):
            edge = random.choice(['top', 'bottom', 'left', 'right'])
            if edge == 'top': zx, zy = random.randint(0, max_w), 0
            elif edge == 'bottom': zx, zy = random.randint(0, max_w), max_h
            elif edge == 'left': zx, zy = 0, random.randint(0, max_h)
            else: zx, zy = max_w, random.randint(0, max_h)
            if not any(math.hypot(b.x - zx, b.y - zy) < 1000 for b in bases) and not is_obstacle(zx, zy): return zx, zy
        return 0, 0
    
    res = {'wood': 200, 'crystals': 100} 
    buildings = [Building(base_spawn_col, base_spawn_row, 'base')]
    buildings[0].is_built, buildings[0].hp = True, buildings[0].max_hp
    for cc, cr in cemetery_data: buildings.append(Building(cc, cr, 'cemetery'))
    trees = [Tree(tx, ty) for tx, ty in trees_data if not is_obstacle(tx, ty)]
    crystals = [Crystal(cx, cy) for cx, cy in crystals_data if not is_obstacle(cx, cy)]
    
    base_x_pixel = (base_spawn_col * TILE_SIZE) + TILE_SIZE
    base_y_pixel = (base_spawn_row * TILE_SIZE) + TILE_SIZE
    units = [Unit(base_x_pixel + 80, base_y_pixel + i * 30, 'worker') for i in range(3)]
    zombies, visual_effects = [], []
    
    camera_x, camera_y, CAMERA_SPEED, SCROLL_MARGIN, OOB_MARGIN = 0, 0, 15, 20, 300
    is_selecting, selection_start_world, pending_command, wall_rotation, zoom = False, (0, 0), None, 0, 1.0 
    
    worker_menu_state = 'MAIN'
    
    global_time = int(day_length_frames * (8.0 / 24.0)) 
    current_day = 1
    horde_spawned = False 
    last_click_time, last_clicked_type = 0, None
    
    SCALE_X, SCALE_Y = MINIMAP_SIZE / WORLD_WIDTH, MINIMAP_SIZE / WORLD_HEIGHT
    minimap_bg = pygame.Surface((MINIMAP_SIZE, MINIMAP_SIZE))
    minimap_bg.fill(GRASS_COLOR) 
    for r in range(MAP_ROWS):
        for c in range(MAP_COLS):
            val = game_map[r][c]
            rect = (c * TILE_SIZE * SCALE_X, r * TILE_SIZE * SCALE_Y, TILE_SIZE * SCALE_X, TILE_SIZE * SCALE_Y)
            if val == 1: pygame.draw.rect(minimap_bg, ROCK_COLOR, rect)
            elif val == 5: pygame.draw.rect(minimap_bg, WATER_COLOR, rect)
            elif val == 6: pygame.draw.rect(minimap_bg, DIRT_COLOR, rect)
    
    fog_surface = pygame.Surface((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    
    is_paused = False
    is_fullscreen = False
    exit_to_menu = False
    running = True

    while running:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        VIEW_HEIGHT = HEIGHT - TOP_BAR_HEIGHT - UI_HEIGHT
        BOTTOM_UI_Y = HEIGHT - UI_HEIGHT
        v_width, v_height = WIDTH / zoom, VIEW_HEIGHT / zoom
        
        minimap_rect = pygame.Rect(20, BOTTOM_UI_Y + 10, MINIMAP_SIZE, MINIMAP_SIZE)
        if not is_paused and pygame.mouse.get_pressed()[0] and minimap_rect.collidepoint(mouse_x, mouse_y):
            camera_x = ((mouse_x - 20) / MINIMAP_SIZE) * WORLD_WIDTH - (v_width / 2)
            camera_y = ((mouse_y - (BOTTOM_UI_Y + 10)) / MINIMAP_SIZE) * WORLD_HEIGHT - (v_height / 2)
    
        world_mouse_x = (mouse_x / zoom) + camera_x
        world_mouse_y = ((mouse_y - TOP_BAR_HEIGHT) / zoom) + camera_y
    
        current_pop = len([u for u in units if not u.is_hidden])
        max_pop = 5 + (sum(1 for b in buildings if b.is_built and b.b_type in ['house', 'base']) * 5)
        
        time_ratio = (global_time % day_length_frames) / day_length_frames
        hour, minutes = int(time_ratio * 24), int((time_ratio * 24 % 1) * 60)
        time_str = f"Dzień {current_day} - {hour:02d}:{minutes:02d}"
        
        phase_name, is_night = "Dzień", False
        if 18 <= hour < 20: phase_name = "Zmierzch"
        elif 20 <= hour or hour < 4: phase_name, is_night = "Noc", True
        elif 4 <= hour < 6: phase_name = "Świt"
    
        has_house = any(b.b_type == 'house' and b.is_built for b in buildings)
        has_workshop = any(b.b_type == 'workshop' and b.is_built for b in buildings)
    
        active_buttons = []
        selected_workers = sum(1 for u in units if u.is_selected and u.u_type == 'worker' and not u.is_hidden)
        selected_bases = [b for b in buildings if b.is_selected and b.b_type == 'base' and b.is_built]
        selected_barracks = [b for b in buildings if b.is_selected and b.b_type == 'barracks' and b.is_built]
        selected_obs_towers = [b for b in buildings if b.is_selected and b.b_type == 'obs_tower' and getattr(b, 'garrisoned_unit', None)]
        
        if selected_bases:
            w_cost = UNIT_STATS['worker']
            active_buttons.append({'id': 'R_WORKER', 'label': 'Robotnik', 'w': w_cost['cost_wood'], 'c': w_cost['cost_crystal'], 'hotkey': 'R', 'col': 0, 'row': 0})
            if selected_bases[0].recruit_queue > 0: active_buttons.append({'id': 'CANCEL_B', 'label': 'Anuluj', 'w': 0, 'c': 0, 'hotkey': 'Esc', 'col': 1, 'row': 0})
        elif selected_barracks:
            a_cost = UNIT_STATS['archer']
            active_buttons.append({'id': 'R_ARCHER', 'label': 'Łucznik', 'w': a_cost['cost_wood'], 'c': a_cost['cost_crystal'], 'hotkey': 'A', 'col': 0, 'row': 0})
            if selected_barracks[0].recruit_queue > 0: active_buttons.append({'id': 'CANCEL_B', 'label': 'Anuluj', 'w': 0, 'c': 0, 'hotkey': 'Esc', 'col': 1, 'row': 0})
        elif selected_obs_towers:
            active_buttons.append({'id': 'UNGARRISON', 'label': 'Wyprowadź', 'w': 0, 'c': 0, 'hotkey': 'U', 'col': 0, 'row': 0})
        elif selected_workers > 0:
            bst = BUILDING_STATS
            if worker_menu_state == 'MAIN':
                active_buttons.append({'id': 'MENU_BASIC', 'label': 'Budowle Podst.', 'w': 0, 'c': 0, 'hotkey': '1', 'col': 0, 'row': 0})
                active_buttons.append({'id': 'MENU_ADV', 'label': 'Budowle Zaaw.', 'w': 0, 'c': 0, 'hotkey': '2', 'col': 1, 'row': 0})
                active_buttons.append({'id': 'CMD_REPAIR', 'label': 'Napraw', 'w': 0, 'c': 0, 'hotkey': 'N', 'col': 2, 'row': 0})
            elif worker_menu_state == 'BASIC':
                active_buttons.append({'id': 'B_BASE', 'label': 'Baza', 'w': bst['base']['cost_w'], 'c': bst['base']['cost_c'], 'hotkey': 'Q', 'col': 0, 'row': 0})
                active_buttons.append({'id': 'B_HOUSE', 'label': 'Magazyn', 'w': bst['house']['cost_w'], 'c': bst['house']['cost_c'], 'hotkey': 'H', 'col': 1, 'row': 0})
                active_buttons.append({'id': 'B_WALL', 'label': 'Mur', 'w': bst['wall']['cost_w'], 'c': bst['wall']['cost_c'], 'hotkey': 'W', 'col': 2, 'row': 0})
                active_buttons.append({'id': 'B_TOWER', 'label': 'Wieżyczka', 'w': bst['tower']['cost_w'], 'c': bst['tower']['cost_c'], 'hotkey': 'T', 'col': 3, 'row': 0})
                active_buttons.append({'id': 'B_OBSTOWER', 'label': 'Wieża Obs.', 'w': bst['obs_tower']['cost_w'], 'c': bst['obs_tower']['cost_c'], 'hotkey': 'O', 'col': 4, 'row': 0})
                active_buttons.append({'id': 'B_WORKSHOP', 'label': 'Warsztat', 'w': bst['workshop']['cost_w'], 'c': bst['workshop']['cost_c'], 'hotkey': 'K', 'col': 5, 'row': 0, 'disabled': not has_house})
                active_buttons.append({'id': 'MENU_BACK', 'label': 'Wróć', 'w': 0, 'c': 0, 'hotkey': 'Esc', 'col': 6, 'row': 0})
            elif worker_menu_state == 'ADV':
                active_buttons.append({'id': 'B_BARRACKS', 'label': 'Baraki', 'w': bst['barracks']['cost_w'], 'c': bst['barracks']['cost_c'], 'hotkey': 'B', 'col': 0, 'row': 0, 'disabled': not has_workshop})
                active_buttons.append({'id': 'B_DOUBLETOWER', 'label': 'Podwójne Dzi.', 'w': bst['double_tower']['cost_w'], 'c': bst['double_tower']['cost_c'], 'hotkey': 'D', 'col': 1, 'row': 0, 'disabled': not has_workshop})
                active_buttons.append({'id': 'MENU_BACK', 'label': 'Wróć', 'w': 0, 'c': 0, 'hotkey': 'Esc', 'col': 2, 'row': 0})
    
        cmd_card_start_x, cmd_card_start_y = WIDTH - 650, BOTTOM_UI_Y + 15
        for btn in active_buttons:
            btn['rect'] = pygame.Rect(cmd_card_start_x + (btn['col'] * 90), cmd_card_start_y + (btn['row'] * 60), 80, 50)
    
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.VIDEORESIZE:
                if not is_fullscreen:
                    WIDTH, HEIGHT = event.w, event.h
                    VIEW_HEIGHT = HEIGHT - TOP_BAR_HEIGHT - UI_HEIGHT
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                    fog_surface = pygame.Surface((WIDTH, HEIGHT)) 
                
            elif event.type == pygame.MOUSEWHEEL and not is_paused:
                if pending_command == 'BUILD_wall': wall_rotation = 1 - wall_rotation 
                else: zoom = max(0.5, min(zoom + event.y * 0.1, 2.0))
                    
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        WIDTH, HEIGHT = screen.get_size()
                    else:
                        WIDTH, HEIGHT = 1024, 768
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                    VIEW_HEIGHT = HEIGHT - TOP_BAR_HEIGHT - UI_HEIGHT
                    fog_surface = pygame.Surface((WIDTH, HEIGHT))
                    continue
                    
                if is_paused:
                    if event.key in [pygame.K_ESCAPE, pygame.K_F10]: is_paused = False
                    continue

                if event.key == pygame.K_F10:
                    is_paused = True
                elif event.key == pygame.K_ESCAPE:
                    if pending_command: pending_command = None
                    elif worker_menu_state in ['BASIC', 'ADV']: worker_menu_state = 'MAIN'
                    elif any(o.is_selected for o in units + buildings + trees + crystals + zombies):
                        for o in units + buildings + trees + crystals + zombies: o.is_selected = False
                    else:
                        is_paused = True
                elif event.key == pygame.K_s:
                    for u in units:
                        if u.is_selected: u.command_stop()
                    pending_command = None
                elif event.key == pygame.K_m: pending_command = 'MOVE'
                elif event.key == pygame.K_a:
                    if selected_barracks:
                        a_cost = UNIT_STATS['archer']
                        if current_pop + selected_barracks[0].recruit_queue >= max_pop: show_message("Limit Populacji!")
                        elif res['wood'] >= a_cost['cost_wood'] and res['crystals'] >= a_cost['cost_crystal']: 
                            res['wood'] -= a_cost['cost_wood']; res['crystals'] -= a_cost['cost_crystal']; selected_barracks[0].recruit_queue += 1
                    else: pending_command = 'ATTACK'
                elif event.key == pygame.K_u and selected_obs_towers:
                    for b in selected_obs_towers:
                        if b.garrisoned_unit:
                            u_ref = b.garrisoned_unit
                            b.garrisoned_unit = None
                            u_ref.is_hidden = False
                            u_ref.building_ref = None
                            u_ref.finish_current_task(game_map, MAP_COLS, MAP_ROWS, buildings)
                elif event.key == pygame.K_r and selected_bases:
                    w_cost = UNIT_STATS['worker']
                    if current_pop + selected_bases[0].recruit_queue >= max_pop: show_message("Limit Populacji!")
                    elif res['wood'] >= w_cost['cost_wood']: res['wood'] -= w_cost['cost_wood']; selected_bases[0].recruit_queue += 1
                elif selected_workers > 0:
                    if event.key == pygame.K_n: pending_command = 'REPAIR'
                    elif worker_menu_state == 'MAIN':
                        if event.key == pygame.K_1: worker_menu_state = 'BASIC'
                        elif event.key == pygame.K_2: worker_menu_state = 'ADV'
                    elif worker_menu_state == 'BASIC':
                        if event.key == pygame.K_h: pending_command = 'BUILD_house'
                        elif event.key == pygame.K_w: pending_command = 'BUILD_wall'
                        elif event.key == pygame.K_q: pending_command = 'BUILD_base'
                        elif event.key == pygame.K_t: pending_command = 'BUILD_tower'
                        elif event.key == pygame.K_o: pending_command = 'BUILD_obs_tower'
                        elif event.key == pygame.K_k:
                            if has_house: pending_command = 'BUILD_workshop'
                    elif worker_menu_state == 'ADV':
                        if event.key == pygame.K_b and has_workshop: pending_command = 'BUILD_barracks'
                        elif event.key == pygame.K_d and has_workshop: pending_command = 'BUILD_double_tower'
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if is_paused:
                    if event.button == 1:
                        resume_rect = pygame.Rect(WIDTH//2 - 125, HEIGHT//2 - 30, 250, 60)
                        exit_rect = pygame.Rect(WIDTH//2 - 125, HEIGHT//2 + 50, 250, 60)
                        if resume_rect.collidepoint(mouse_x, mouse_y): is_paused = False
                        elif exit_rect.collidepoint(mouse_x, mouse_y): exit_to_menu = True; running = False
                    continue

                if event.button == 1:
                    mods = pygame.key.get_mods()
                    shift_pressed = bool(mods & pygame.KMOD_SHIFT)
                    
                    if minimap_rect.collidepoint(mouse_x, mouse_y) or mouse_y < TOP_BAR_HEIGHT: continue
                    elif mouse_y >= BOTTOM_UI_Y:
                        clicked_ui = False
                        for btn in active_buttons:
                            if btn['rect'].collidepoint(mouse_x, mouse_y):
                                clicked_ui = True
                                if btn.get('disabled'): show_message("Wymagania niespełnione!")
                                elif btn['id'] == 'MENU_BASIC': worker_menu_state = 'BASIC'
                                elif btn['id'] == 'MENU_ADV': worker_menu_state = 'ADV'
                                elif btn['id'] == 'MENU_BACK': worker_menu_state = 'MAIN'
                                elif btn['id'] == 'CMD_REPAIR': pending_command = 'REPAIR'
                                elif btn['id'] == 'R_WORKER' and selected_bases:
                                    w_cost = UNIT_STATS['worker']
                                    if current_pop + selected_bases[0].recruit_queue >= max_pop: show_message("Limit Populacji!")
                                    elif res['wood'] >= w_cost['cost_wood']: res['wood'] -= w_cost['cost_wood']; selected_bases[0].recruit_queue += 1
                                elif btn['id'] == 'R_ARCHER' and selected_barracks:
                                    a_cost = UNIT_STATS['archer']
                                    if current_pop + selected_barracks[0].recruit_queue >= max_pop: show_message("Limit Populacji!")
                                    elif res['wood'] >= a_cost['cost_wood'] and res['crystals'] >= a_cost['cost_crystal']: 
                                        res['wood'] -= a_cost['cost_wood']; res['crystals'] -= a_cost['cost_crystal']; selected_barracks[0].recruit_queue += 1
                                elif btn['id'] == 'CANCEL_B':
                                    if selected_bases and selected_bases[0].recruit_queue > 0:
                                        selected_bases[0].recruit_queue -= 1; res['wood'] += UNIT_STATS['worker']['cost_wood']
                                    elif selected_barracks and selected_barracks[0].recruit_queue > 0:
                                        selected_barracks[0].recruit_queue -= 1; res['wood'] += UNIT_STATS['archer']['cost_wood']; res['crystals'] += UNIT_STATS['archer']['cost_crystal']
                                elif btn['id'] == 'UNGARRISON':
                                    for b in selected_obs_towers:
                                        if b.garrisoned_unit:
                                            u_ref = b.garrisoned_unit
                                            b.garrisoned_unit = None
                                            u_ref.is_hidden = False
                                            u_ref.building_ref = None
                                            u_ref.finish_current_task(game_map, MAP_COLS, MAP_ROWS, buildings)
                                elif btn['id'].startswith('B_'): pending_command = 'BUILD_' + btn['id'].replace('B_', '').lower()
                        if not clicked_ui: pending_command = None
                    
                    else:
                        if pending_command in ['MOVE', 'ATTACK', 'REPAIR']:
                            target_entity = None
                            if pending_command == 'ATTACK':
                                target_entity = next((z for z in reversed(zombies) if math.hypot(z.x - world_mouse_x, z.y - world_mouse_y) <= z.radius), None)
                                if not target_entity: target_entity = next((u for u in reversed(units) if math.hypot(u.x - world_mouse_x, u.y - world_mouse_y) <= u.radius), None)
                                if not target_entity: target_entity = next((b for b in buildings if b.rect.collidepoint(world_mouse_x, world_mouse_y)), None)
                            elif pending_command == 'REPAIR':
                                target_entity = next((b for b in buildings if b.rect.collidepoint(world_mouse_x, world_mouse_y)), None)
                                
                            for u in units:
                                if u.is_selected:
                                    if pending_command == 'ATTACK' and target_entity: u.issue_command(('ATTACK', target_entity), shift_pressed, game_map, MAP_COLS, MAP_ROWS, buildings)
                                    elif pending_command == 'REPAIR' and target_entity and target_entity.hp < target_entity.max_hp and u.u_type == 'worker': 
                                        u.issue_command(('REPAIR', target_entity), shift_pressed, game_map, MAP_COLS, MAP_ROWS, buildings)
                                    elif pending_command == 'MOVE': u.issue_command(('MOVE', world_mouse_x, world_mouse_y), shift_pressed, game_map, MAP_COLS, MAP_ROWS, buildings)
                            if not shift_pressed: pending_command = None; 
                            continue
                            
                        elif pending_command and pending_command.startswith('BUILD_'):
                            b_type = pending_command.replace('BUILD_', '')
                            if b_type == 'obstower': b_type = 'obs_tower'
                            elif b_type == 'doubletower': b_type = 'double_tower'
                            st = BUILDING_STATS[b_type]
                            t_col, t_row = int(world_mouse_x // TILE_SIZE), int(world_mouse_y // TILE_SIZE)
                            
                            can_build = True
                            for r_check in range(t_row, t_row + st['h_tiles']):
                                for c_check in range(t_col, t_col + st['w_tiles']):
                                    if is_obstacle(c_check * TILE_SIZE, r_check * TILE_SIZE): can_build = False
                            
                            check_rect = pygame.Rect(t_col * TILE_SIZE, t_row * TILE_SIZE, st['w_tiles'] * TILE_SIZE, st['h_tiles'] * TILE_SIZE)
                            if any(b.rect.colliderect(check_rect) for b in buildings): can_build = False
                            
                            if can_build:
                                if res['wood'] >= st['cost_w'] and res['crystals'] >= st['cost_c']:
                                    res['wood'] -= st['cost_w']; res['crystals'] -= st['cost_c']
                                    new_b = Building(t_col, t_row, b_type)
                                    buildings.append(new_b)
                                    for u in units:
                                        if u.is_selected and u.u_type == 'worker' and not u.is_hidden: 
                                            u.issue_command(('BUILD', new_b), shift_pressed, game_map, MAP_COLS, MAP_ROWS, buildings)
                                else: show_message("Brak surowców na budowę!")
                            if not shift_pressed and b_type != 'wall': pending_command = None 
                            continue
    
                        current_time = pygame.time.get_ticks()
                        clicked_u = next((u for u in reversed(units) if not u.is_hidden and math.hypot(u.x - world_mouse_x, u.y - world_mouse_y) <= u.radius), None)
                        clicked_b = next((b for b in buildings if b.rect.collidepoint(world_mouse_x, world_mouse_y)), None)
                        clicked_c = next((c for c in crystals if math.hypot(c.x - world_mouse_x, c.y - world_mouse_y) <= c.radius), None)
                        clicked_t = next((t for t in trees if math.hypot(t.x - world_mouse_x, t.y - world_mouse_y) <= t.radius), None)
    
                        if clicked_u:
                            if current_time - last_click_time < 300 and last_clicked_type == clicked_u.title:
                                for u in units: u.is_selected = False
                                for u in units:
                                    if not u.is_hidden and u.title == clicked_u.title and math.hypot(u.x - clicked_u.x, u.y - clicked_u.y) < 400: u.is_selected = True
                            else:
                                for o in units + buildings + trees + crystals + zombies: o.is_selected = False
                                clicked_u.is_selected = True
                            last_clicked_type = clicked_u.title; last_click_time = current_time
                        elif clicked_b or clicked_c or clicked_t:
                            for o in units + buildings + trees + crystals + zombies: o.is_selected = False
                            if clicked_b: clicked_b.is_selected = True
                            elif clicked_c: clicked_c.is_selected = True
                            elif clicked_t: clicked_t.is_selected = True
                            last_clicked_type = None
                        else:
                            for o in units + buildings + trees + crystals + zombies: o.is_selected = False
                            is_selecting, selection_start_world = True, (world_mouse_x, world_mouse_y)
                
                elif event.button == 3 and not is_paused: 
                    if TOP_BAR_HEIGHT <= mouse_y < BOTTOM_UI_Y:
                        mods = pygame.key.get_mods()
                        shift_pressed = bool(mods & pygame.KMOD_SHIFT)
                        
                        pending_command = None
                        if selected_bases: selected_bases[0].rally_x, selected_bases[0].rally_y = world_mouse_x, world_mouse_y
                        elif selected_barracks: selected_barracks[0].rally_x, selected_barracks[0].rally_y = world_mouse_x, world_mouse_y
                        else:
                            clicked_res = next((t for t in trees if math.hypot(t.x - world_mouse_x, t.y - world_mouse_y) <= t.radius), None)
                            if not clicked_res: clicked_res = next((c for c in crystals if math.hypot(c.x - world_mouse_x, c.y - world_mouse_y) <= c.radius), None)
                            clicked_enemy = next((z for z in reversed(zombies) if math.hypot(z.x - world_mouse_x, z.y - world_mouse_y) <= z.radius), None)
                            clicked_b = next((b for b in buildings if b.rect.collidepoint(world_mouse_x, world_mouse_y)), None)
                            
                            for u in units:
                                if u.is_selected and not u.is_hidden:
                                    if clicked_b and u.u_type == 'worker':
                                        if not clicked_b.is_built:
                                            u.issue_command(('BUILD', clicked_b), shift_pressed, game_map, MAP_COLS, MAP_ROWS, buildings)
                                        elif clicked_b.b_type == 'obs_tower': 
                                            u.issue_command(('GARRISON', clicked_b), shift_pressed, game_map, MAP_COLS, MAP_ROWS, buildings)
                                        elif clicked_b.hp < clicked_b.max_hp: 
                                            u.issue_command(('REPAIR', clicked_b), shift_pressed, game_map, MAP_COLS, MAP_ROWS, buildings)
                                        else:
                                            u.issue_command(('MOVE', world_mouse_x, world_mouse_y), shift_pressed, game_map, MAP_COLS, MAP_ROWS, buildings)
                                    elif clicked_enemy: 
                                        u.issue_command(('ATTACK', clicked_enemy), shift_pressed, game_map, MAP_COLS, MAP_ROWS, buildings)
                                    elif clicked_res and u.u_type == 'worker': 
                                        u.issue_command(('HARVEST', clicked_res), shift_pressed, game_map, MAP_COLS, MAP_ROWS, buildings)
                                    else: 
                                        u.issue_command(('MOVE', world_mouse_x, world_mouse_y), shift_pressed, game_map, MAP_COLS, MAP_ROWS, buildings)
    
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and is_selecting and not is_paused:
                    is_selecting = False
                    w, h = abs(selection_start_world[0] - world_mouse_x), abs(selection_start_world[1] - world_mouse_y)
                    rect = pygame.Rect(min(selection_start_world[0], world_mouse_x), min(selection_start_world[1], world_mouse_y), w, h)
                    for u in units:
                        if not u.is_hidden and rect.collidepoint(u.x, u.y): u.is_selected = True
    
        if not is_paused:
            if mouse_x < SCROLL_MARGIN: camera_x -= CAMERA_SPEED
            elif mouse_x > WIDTH - SCROLL_MARGIN: camera_x += CAMERA_SPEED
            if mouse_y < SCROLL_MARGIN: camera_y -= CAMERA_SPEED
            elif mouse_y > HEIGHT - SCROLL_MARGIN: camera_y += CAMERA_SPEED
            
            camera_x = max(-OOB_MARGIN, min(camera_x, WORLD_WIDTH - v_width + OOB_MARGIN))
            camera_y = max(-OOB_MARGIN, min(camera_y, WORLD_HEIGHT - v_height + OOB_MARGIN))
        
            global_time += 1
            new_day = (global_time // day_length_frames) + 1
            if new_day > current_day: 
                current_day, horde_spawned = new_day, False 

            current_global_hour = (current_day - 1) * 24 + hour

            if phase_name == "Noc":
                if current_day == horde_day and hour == 20 and not horde_spawned:
                    show_message(f"Horda Zombie atakuje! ({horde_size} zainfekowanych)")
                    for _ in range(horde_size):
                        zx, zy = get_zombie_spawn_point(buildings, WORLD_WIDTH, WORLD_HEIGHT)
                        if zx: zombies.append(Zombie(zx, zy))
                    horde_spawned = True
                    
            if current_global_hour > 0 and current_global_hour % wave_interval_hours == 0 and current_global_hour > last_wave_spawn_hour_global:
                show_message(f"Cykliczna fala zombie! ({wave_size} z zewnątrz)")
                for _ in range(wave_size):
                    zx, zy = get_zombie_spawn_point(buildings, WORLD_WIDTH, WORLD_HEIGHT)
                    if zx: zombies.append(Zombie(zx, zy))
                last_wave_spawn_hour_global = current_global_hour

            if global_message_timer > 0: global_message_timer -= 1

            for b in buildings:
                result = b.update(zombies, visual_effects, is_night)
                if result == 'spawn_worker':
                    u = Unit(b.rect.centerx, b.rect.centery, 'worker'); u.issue_command(('MOVE', b.rally_x, b.rally_y), False, game_map, MAP_COLS, MAP_ROWS, buildings); units.append(u)
                elif result == 'spawn_archer':
                    u = Unit(b.rect.centerx, b.rect.centery, 'archer'); u.issue_command(('MOVE', b.rally_x, b.rally_y), False, game_map, MAP_COLS, MAP_ROWS, buildings); units.append(u)
                elif result == 'spawn_zombie': zombies.append(Zombie(b.rect.centerx, b.rect.centery + 40))
        
            for u in units: u.update(res, buildings, trees, crystals, zombies, is_obstacle, get_speed_mod, visual_effects, game_map, MAP_COLS, MAP_ROWS, units)
            for z in zombies: z.update(units, buildings, is_obstacle, get_speed_mod, visual_effects, game_map, MAP_COLS, MAP_ROWS)
            
            for ef in visual_effects: ef['timer'] -= 1
            visual_effects = [ef for ef in visual_effects if ef['timer'] > 0]
            
            resolve_collisions(units, buildings, is_obstacle)
            resolve_collisions(zombies, buildings, is_obstacle)
            
            trees = [t for t in trees if t.hp > 0]; crystals = [c for c in crystals if c.hp > 0]
            units = [u for u in units if u.hp > 0]; buildings = [b for b in buildings if b.hp > 0]
            zombies = [z for z in zombies if z.hp > 0]
    
        if fog_surface.get_size() != (int(v_width), int(v_height)):
            fog_surface = pygame.Surface((int(v_width), int(v_height)), pygame.SRCALPHA)
            
        fog_surface.fill((0, 0, 0, 255))
        
        for u in units: 
            if not u.is_hidden: pygame.draw.circle(fog_surface, (0, 0, 0, 0), (int(u.x - camera_x), int(u.y - camera_y)), int(u.vision_range))
        for b in buildings: 
            if b.is_built and b.b_type != 'cemetery': 
                pygame.draw.circle(fog_surface, (0, 0, 0, 0), (int(b.rect.centerx - camera_x), int(b.rect.centery - camera_y)), int(b.vision_range))
        
        def is_in_vision(world_x, world_y):
            for u in units:
                if not u.is_hidden and (u.x - world_x)**2 + (u.y - world_y)**2 <= u.vision_range**2: return True
            for b in buildings:
                if b.is_built and b.b_type != 'cemetery' and (b.rect.centerx - world_x)**2 + (b.rect.centery - world_y)**2 <= b.vision_range**2: return True
            return False
    
        screen.fill(BLACK)
        world_surface = pygame.Surface((v_width, v_height))
        world_surface.fill(GRASS_COLOR)
    
        start_col, end_col = int(camera_x // TILE_SIZE), int((camera_x + v_width) // TILE_SIZE) + 1
        start_row, end_row = int(camera_y // TILE_SIZE), int((camera_y + v_height) // TILE_SIZE) + 1
    
        for row in range(max(0, start_row), min(MAP_ROWS, end_row)):
            for col in range(max(0, start_col), min(MAP_COLS, end_col)):
                val = game_map[row][col]
                rect = ((col * TILE_SIZE) - camera_x, (row * TILE_SIZE) - camera_y, TILE_SIZE, TILE_SIZE)
                if val == 1: pygame.draw.rect(world_surface, ROCK_COLOR, rect)
                elif val == 5: pygame.draw.rect(world_surface, WATER_COLOR, rect)
                elif val == 6: pygame.draw.rect(world_surface, DIRT_COLOR, rect)
    
        for b in buildings:
            if is_visible(b, camera_x, camera_y, v_width, v_height):
                if b.b_type != 'cemetery' or is_in_vision(b.rect.centerx, b.rect.centery):
                    b.draw(world_surface, camera_x, camera_y)
                    
        for c in crystals:
            if is_visible(c, camera_x, camera_y, v_width, v_height):
                cx, cy = int(c.x - camera_x), int(c.y - camera_y)
                pygame.draw.circle(world_surface, c.color, (cx, cy), c.radius); c.draw_hp(world_surface, camera_x, camera_y)
                if c.is_selected: pygame.draw.circle(world_surface, WHITE, (cx, cy), c.radius + 2, 1)
        for t in trees:
            if is_visible(t, camera_x, camera_y, v_width, v_height):
                tx, ty = int(t.x - camera_x), int(t.y - camera_y)
                pygame.draw.circle(world_surface, t.color, (tx, ty), t.radius); t.draw_hp(world_surface, camera_x, camera_y)
                if t.is_selected: pygame.draw.circle(world_surface, WHITE, (tx, ty), t.radius + 2, 1)
        for u in units:
            if not u.is_hidden and is_visible(u, camera_x, camera_y, v_width, v_height): u.draw(world_surface, camera_x, camera_y)
        
        for z in zombies:
            if is_visible(z, camera_x, camera_y, v_width, v_height) and is_in_vision(z.x, z.y): 
                z.draw(world_surface, camera_x, camera_y)
            
        for ef in visual_effects:
            pygame.draw.line(world_surface, ef['color'], (ef['x1'] - camera_x, ef['y1'] - camera_y), (ef['x2'] - camera_x, ef['y2'] - camera_y), 2)
    
        if is_selecting:
            pygame.draw.rect(world_surface, GREEN, (min(selection_start_world[0], world_mouse_x) - camera_x, 
                                                    min(selection_start_world[1], world_mouse_y) - camera_y, 
                                                    abs(selection_start_world[0] - world_mouse_x), 
                                                    abs(selection_start_world[1] - world_mouse_y)), 2)
    
        if pending_command == 'ATTACK':
            pygame.draw.circle(world_surface, RED, (int(world_mouse_x - camera_x), int(world_mouse_y - camera_y)), 20, 2)
            pygame.draw.line(world_surface, RED, (world_mouse_x - camera_x - 10, world_mouse_y - camera_y), (world_mouse_x - camera_x + 10, world_mouse_y - camera_y))
            pygame.draw.line(world_surface, RED, (world_mouse_x - camera_x, world_mouse_y - camera_y - 10), (world_mouse_x - camera_x, world_mouse_y - camera_y + 10))
        elif pending_command == 'REPAIR':
            pygame.draw.circle(world_surface, GREEN, (int(world_mouse_x - camera_x), int(world_mouse_y - camera_y)), 15, 2)
            pygame.draw.line(world_surface, GREEN, (world_mouse_x - camera_x - 8, world_mouse_y - camera_y), (world_mouse_x - camera_x + 8, world_mouse_y - camera_y))
            pygame.draw.line(world_surface, GREEN, (world_mouse_x - camera_x, world_mouse_y - camera_y - 8), (world_mouse_x - camera_x, world_mouse_y - camera_y + 8))
        elif pending_command and pending_command.startswith('BUILD_'):
            b_type = pending_command.replace('BUILD_', '')
            if b_type == 'obstower': b_type = 'obs_tower'
            elif b_type == 'doubletower': b_type = 'double_tower'
            st = BUILDING_STATS[b_type]
            t_col, t_row = int(world_mouse_x // TILE_SIZE), int(world_mouse_y // TILE_SIZE)
            
            can_build = True
            for r_check in range(t_row, t_row + st['h_tiles']):
                for c_check in range(t_col, t_col + st['w_tiles']):
                    if is_obstacle(c_check * TILE_SIZE, r_check * TILE_SIZE): can_build = False
            
            check_rect = pygame.Rect(t_col * TILE_SIZE, t_row * TILE_SIZE, st['w_tiles'] * TILE_SIZE, st['h_tiles'] * TILE_SIZE)
            if any(b.rect.colliderect(check_rect) for b in buildings): can_build = False
                
            grid_color = (0, 255, 0, 100) if can_build else (255, 0, 0, 100)
            s = pygame.Surface((st['w_tiles'] * TILE_SIZE, st['h_tiles'] * TILE_SIZE), pygame.SRCALPHA)
            s.fill(grid_color)
            pygame.draw.rect(s, (255, 255, 255, 150), (0, 0, st['w_tiles'] * TILE_SIZE, st['h_tiles'] * TILE_SIZE), 2)
            world_surface.blit(s, (t_col * TILE_SIZE - camera_x, t_row * TILE_SIZE - camera_y))
    
        world_surface.blit(fog_surface, (0, 0))
    
        scaled_world = pygame.transform.scale(world_surface, (WIDTH, VIEW_HEIGHT))
        screen.blit(scaled_world, (0, TOP_BAR_HEIGHT)) 

        # INTERFEJS
        pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, TOP_BAR_HEIGHT))
        pygame.draw.line(screen, UI_BORDER, (0, TOP_BAR_HEIGHT), (WIDTH, TOP_BAR_HEIGHT), 2)
        screen.blit(font_bold.render(f"{time_str} | {phase_name}", True, YELLOW if phase_name == "Dzień" else CYAN), (20, 5))
        draw_resource_icon(screen, WIDTH - 420, 15, 'wood'); screen.blit(font_main.render(str(res['wood']), True, WHITE), (WIDTH - 405, 5))
        draw_resource_icon(screen, WIDTH - 300, 15, 'crystal'); screen.blit(font_main.render(str(res['crystals']), True, WHITE), (WIDTH - 285, 5))
        screen.blit(font_main.render(f"Pop: {current_pop}/{max_pop}", True, RED if current_pop >= max_pop else WHITE), (WIDTH - 150, 5))
    
        pygame.draw.rect(screen, DARK_GRAY, (0, BOTTOM_UI_Y, WIDTH, UI_HEIGHT))
        pygame.draw.line(screen, UI_BORDER, (0, BOTTOM_UI_Y), (WIDTH, BOTTOM_UI_Y), 4)
    
        screen.blit(minimap_bg, (20, BOTTOM_UI_Y + 10))
        for u in units: 
            if not u.is_hidden: pygame.draw.rect(screen, BLUE, (20 + int(u.x * SCALE_X), BOTTOM_UI_Y + 10 + int(u.y * SCALE_Y), 2, 2))
        for z in zombies:
            if is_in_vision(z.x, z.y): pygame.draw.rect(screen, RED, (20 + int(z.x * SCALE_X), BOTTOM_UI_Y + 10 + int(z.y * SCALE_Y), 2, 2))
        pygame.draw.rect(screen, WHITE, (20 + int(camera_x * SCALE_X), BOTTOM_UI_Y + 10 + int(camera_y * SCALE_Y), int(v_width * SCALE_X), int(v_height * SCALE_Y)), 1)
        pygame.draw.line(screen, UI_BORDER, (180, BOTTOM_UI_Y), (180, HEIGHT), 2)
    
        info_x = 200
        if selected_bases:
            target = selected_bases[0]
            screen.blit(font_info_title.render(target.title, True, WHITE), (info_x, BOTTOM_UI_Y + 15))
            screen.blit(font_small.render(f"HP: {target.hp} / {target.max_hp}", True, RED), (info_x, BOTTOM_UI_Y + 45))
            if target.recruit_queue > 0:
                screen.blit(font_main.render(f"Produkcja: Robotnik ({target.recruit_queue})", True, LIGHT_GRAY), (info_x, BOTTOM_UI_Y + 70))
                pygame.draw.rect(screen, DARK_GRAY, (info_x, BOTTOM_UI_Y + 95, 160, 12))
                pygame.draw.rect(screen, GREEN, (info_x, BOTTOM_UI_Y + 95, int(160 * (target.recruit_progress / target.recruit_time_max)), 12))
        elif selected_barracks:
            target = selected_barracks[0]
            screen.blit(font_info_title.render(target.title, True, WHITE), (info_x, BOTTOM_UI_Y + 15))
            screen.blit(font_small.render(f"HP: {target.hp} / {target.max_hp}", True, RED), (info_x, BOTTOM_UI_Y + 45))
            if target.recruit_queue > 0:
                screen.blit(font_main.render(f"Produkcja: Łucznik ({target.recruit_queue})", True, LIGHT_GRAY), (info_x, BOTTOM_UI_Y + 70))
                pygame.draw.rect(screen, DARK_GRAY, (info_x, BOTTOM_UI_Y + 95, 160, 12))
                pygame.draw.rect(screen, GREEN, (info_x, BOTTOM_UI_Y + 95, int(160 * (target.recruit_progress / target.recruit_time_max)), 12))
        else:
            selected_buildings = [b for b in buildings if b.is_selected]
            selected_zombies = [z for z in zombies if z.is_selected and is_in_vision(z.x, z.y)]
            if len(selected_buildings) > 0:
                target = selected_buildings[0]
                screen.blit(font_info_title.render(target.title, True, WHITE), (info_x, BOTTOM_UI_Y + 15))
                screen.blit(font_small.render(f"HP: {target.hp} / {target.max_hp}", True, RED), (info_x, BOTTOM_UI_Y + 45))
                bonus = "+5 Populacji" if target.b_type == 'house' else ("Gniazdo potworów" if target.b_type == 'cemetery' else "Struktura gracza")
                screen.blit(font_main.render(bonus if target.is_built else "W budowie...", True, LIGHT_GRAY), (info_x, BOTTOM_UI_Y + 70))
            elif len(selected_zombies) > 0:
                target = selected_zombies[0]
                screen.blit(font_info_title.render(target.title, True, (255, 100, 100)), (info_x, BOTTOM_UI_Y + 15))
                screen.blit(font_small.render(f"HP: {target.hp} / {target.max_hp} | Dmg: {target.damage}", True, RED), (info_x, BOTTOM_UI_Y + 45))
            else:
                selected_crystals = [c for c in crystals if c.is_selected]
                selected_trees = [t for t in trees if t.is_selected]
                if len(selected_crystals) > 0:
                    target = selected_crystals[0]
                    screen.blit(font_info_title.render(target.title, True, CYAN), (info_x, BOTTOM_UI_Y + 15))
                    screen.blit(font_main.render(f"Zasoby: {target.amount} / {target.max_amount}", True, WHITE), (info_x, BOTTOM_UI_Y + 45))
                    screen.blit(font_small.render(f"Zajęte miejsca: {sum(1 for u in units if getattr(u, 'target_obj', None) == target and u.state in ['MOVE', 'HARVEST', 'SEARCH_MOVE'])} / {target.max_workers}", True, LIGHT_GRAY), (info_x, BOTTOM_UI_Y + 70))
                elif len(selected_trees) > 0:
                    target = selected_trees[0]
                    screen.blit(font_info_title.render(target.title, True, GREEN), (info_x, BOTTOM_UI_Y + 15))
                    screen.blit(font_main.render(f"Zasoby: {target.amount} / {target.max_amount}", True, WHITE), (info_x, BOTTOM_UI_Y + 45))
                    screen.blit(font_small.render(f"Zajęte miejsca: {sum(1 for u in units if getattr(u, 'target_obj', None) == target and u.state in ['MOVE', 'HARVEST', 'SEARCH_MOVE'])} / {target.max_workers}", True, LIGHT_GRAY), (info_x, BOTTOM_UI_Y + 70))
                elif len([u for u in units if u.is_selected and not u.is_hidden]) > 0:
                    count = len([u for u in units if u.is_selected and not u.is_hidden])
                    screen.blit(font_info_title.render(f"Zaznaczone jednostki ({count})", True, WHITE), (info_x, BOTTOM_UI_Y + 15))
                    su = next((u for u in units if u.is_selected and not u.is_hidden), None)
                    if su: screen.blit(font_small.render(f"HP: {su.hp}/{su.max_hp} | Atak DMG: {su.damage}", True, RED), (info_x, BOTTOM_UI_Y + 45))
    
        pygame.draw.line(screen, UI_BORDER, (cmd_card_start_x - 20, BOTTOM_UI_Y), (cmd_card_start_x - 20, HEIGHT), 2)
        pygame.draw.rect(screen, (20, 25, 30), (cmd_card_start_x - 20, BOTTOM_UI_Y, WIDTH, UI_HEIGHT)) 
    
        for btn in active_buttons:
            btn_color = (30, 40, 50) if btn.get('disabled') else ((80, 100, 120) if btn.get('active') else (50, 60, 80))
            txt_color = (100, 100, 100) if btn.get('disabled') else WHITE
            
            pygame.draw.rect(screen, btn_color, btn['rect'])
            pygame.draw.rect(screen, UI_BORDER, btn['rect'], 2)
            text_surf = font_main.render(btn['label'], True, txt_color)
            screen.blit(text_surf, (btn['rect'].x + (btn['rect'].width - text_surf.get_width()) // 2, btn['rect'].y + 5))
            
            if btn['w'] > 0 or btn['c'] > 0:
                cx, cy = btn['rect'].x + 5, btn['rect'].y + 35
                if btn['w'] > 0:
                    draw_resource_icon(screen, cx, cy, 'wood'); wsurf = font_small.render(str(btn['w']), True, txt_color)
                    screen.blit(wsurf, (cx + 10, cy - 6)); cx += wsurf.get_width() + 20
                if btn['c'] > 0:
                    draw_resource_icon(screen, cx, cy, 'crystal'); csurf = font_small.render(str(btn['c']), True, txt_color)
                    screen.blit(csurf, (cx + 10, cy - 6))
                
            screen.blit(font_small.render(btn['hotkey'], True, LIGHT_GRAY), (btn['rect'].x + 2, btn['rect'].y + 2))

        if global_message_timer > 0:
            msg_surf = font_bold.render(global_message, True, RED)
            screen.blit(msg_surf, ((WIDTH - msg_surf.get_width()) // 2, TOP_BAR_HEIGHT + 20))

        if is_paused:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            
            p_txt = font_title.render("PAUZA", True, WHITE)
            screen.blit(p_txt, (WIDTH//2 - p_txt.get_width()//2, HEIGHT//2 - 120))
            
            f11_txt = font_main.render("F11 - Pełny ekran / Okno", True, LIGHT_GRAY)
            screen.blit(f11_txt, (WIDTH//2 - f11_txt.get_width()//2, HEIGHT//2 - 70))
            
            resume_rect = pygame.Rect(WIDTH//2 - 125, HEIGHT//2 - 30, 250, 60)
            pygame.draw.rect(screen, BLUE, resume_rect)
            pygame.draw.rect(screen, WHITE, resume_rect, 2)
            res_txt = font_bold.render("Wznów (F10 / Esc)", True, WHITE)
            screen.blit(res_txt, (resume_rect.x + (250 - res_txt.get_width())//2, resume_rect.y + 18))
            
            exit_rect = pygame.Rect(WIDTH//2 - 125, HEIGHT//2 + 50, 250, 60)
            pygame.draw.rect(screen, RED, exit_rect)
            pygame.draw.rect(screen, WHITE, exit_rect, 2)
            ex_txt = font_bold.render("Wyjdź do Menu", True, WHITE)
            screen.blit(ex_txt, (exit_rect.x + (250 - ex_txt.get_width())//2, exit_rect.y + 18))

        pygame.display.flip()
        clock.tick(60)

    if not exit_to_menu:
        break