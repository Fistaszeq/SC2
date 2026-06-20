# main.py
import pygame, math, random, json, os
from config import *
pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("RTS - Rzeka, Biomy, Woda Spowalniająca")

from entities import *

font_main = pygame.font.SysFont(None, 28)
font_small = pygame.font.SysFont(None, 18)
font_bold = pygame.font.SysFont(None, 32, bold=True)

global_message, global_message_timer = "", 0
def show_message(text):
    global global_message, global_message_timer
    global_message = text; global_message_timer = 120 

MAP_COLS, MAP_ROWS = 50, 50
WORLD_WIDTH, WORLD_HEIGHT = MAP_COLS * TILE_SIZE, MAP_ROWS * TILE_SIZE
game_map, trees_data, crystals_data = [], [], []
base_spawn_x, base_spawn_y = 250, 250 
horde_day, horde_size = 3, 20 

# --- GENERATOR BIOMÓW I RZEKI ---
def generate_cool_tactical_map():
    grid = [[0 for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)] # 0 = Trawa
    
    # Przecinająca mapę rzeka (wartość 5)
    river_c = 25
    for r in range(MAP_ROWS):
        # Szerokość rzeki
        for w in range(-2, 3):
            if 0 <= river_c + w < MAP_COLS: grid[r][river_c + w] = 5
        # Meandrowanie
        if random.random() < 0.4: river_c += random.choice([-1, 1])

    # Góry i formacje skalne (wartość 1)
    for r in range(MAP_ROWS):
        for c in range(MAP_COLS):
            if grid[r][c] == 5: continue # Nie stawiaj skał na rzece
            if (r < 3 or r > MAP_ROWS-4 or c < 3 or c > MAP_COLS-4) and random.random() < 0.3:
                grid[r][c] = 1
            if c == 35 and not (12 < r < 18 or 32 < r < 38): grid[r][c] = 1

    # Teren startowy (Ziemia - wartość 6)
    for r in range(2, 12):
        for c in range(2, 12):
            if grid[r][c] not in [1, 5]: grid[r][c] = 6

    return grid

if os.path.exists('custom_map.json'):
    with open('custom_map.json', 'r') as f: map_data = json.load(f)
    MAP_COLS, MAP_ROWS = map_data["cols"], map_data["rows"]
    WORLD_WIDTH, WORLD_HEIGHT = MAP_COLS * TILE_SIZE, MAP_ROWS * TILE_SIZE
    horde_day = map_data.get("horde_day", 3)
    horde_size = map_data.get("horde_size", 20)
    game_map = map_data["grid"]
    
    for r in range(MAP_ROWS):
        for c in range(MAP_COLS):
            val = game_map[r][c]
            rx, ry = c * TILE_SIZE + TILE_SIZE//2, r * TILE_SIZE + TILE_SIZE//2
            if val == 2: trees_data.append((rx, ry)); game_map[r][c] = 0
            elif val == 3: crystals_data.append((rx, ry)); game_map[r][c] = 0 
            elif val == 4: base_spawn_x, base_spawn_y = rx, ry; game_map[r][c] = 0
else:
    game_map = generate_cool_tactical_map()
    for _ in range(15): trees_data.append((random.randint(100, 450), random.randint(450, 550)))
    for _ in range(8): crystals_data.append((random.randint(450, 550), random.randint(100, 400)))
    for _ in range(20): trees_data.append((random.randint(1300, 1600), random.randint(600, 1200)))
    for _ in range(12): crystals_data.append((random.randint(1400, 1700), random.randint(1300, 1600)))

def is_obstacle(x, y):
    col, row = int(x // TILE_SIZE), int(y // TILE_SIZE)
    if 0 <= row < MAP_ROWS and 0 <= col < MAP_COLS: return game_map[row][col] == 1
    return True

# --- MODYFIKATOR PRĘDKOŚCI WODY ---
def get_speed_mod(x, y):
    col, row = int(x // TILE_SIZE), int(y // TILE_SIZE)
    if 0 <= row < MAP_ROWS and 0 <= col < MAP_COLS:
        if game_map[row][col] == 5: return 0.5 # Połowa prędkości w rzece
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

# --- INICJALIZACJA DANYCH ---
res = {'wood': 100, 'crystals': 50} 
buildings = [Building(base_spawn_x, base_spawn_y, 'base')]
buildings[0].is_built = True 
buildings[0].hp = buildings[0].max_hp

buildings.append(Building(2300, 200, 'cemetery'))
buildings.append(Building(2300, 2200, 'cemetery'))
buildings.append(Building(200, 2200, 'cemetery'))

trees = [Tree(tx, ty) for tx, ty in trees_data if not is_obstacle(tx, ty)]
crystals = [Crystal(cx, cy) for cx, cy in crystals_data if not is_obstacle(cx, cy)]
units = [Unit(base_spawn_x + 80, base_spawn_y + i * 30, 'worker') for i in range(3)]
zombies = []
visual_effects = []

camera_x, camera_y, CAMERA_SPEED, SCROLL_MARGIN, OOB_MARGIN = 0, 0, 15, 20, 300
is_selecting, selection_start_world, pending_command, wall_rotation, zoom = False, (0, 0), None, 0, 1.0 

global_time = 3200 
current_day = 1
horde_spawned = False
last_click_time, last_clicked_type = 0, None

SCALE_X, SCALE_Y = MINIMAP_SIZE / WORLD_WIDTH, MINIMAP_SIZE / WORLD_HEIGHT
minimap_bg = pygame.Surface((MINIMAP_SIZE, MINIMAP_SIZE))
minimap_bg.fill(GRASS_COLOR) 

# Renderowanie Minimapy w nowych kolorach
for r in range(MAP_ROWS):
    for c in range(MAP_COLS):
        val = game_map[r][c]
        rect = (c * TILE_SIZE * SCALE_X, r * TILE_SIZE * SCALE_Y, TILE_SIZE * SCALE_X, TILE_SIZE * SCALE_Y)
        if val == 1: pygame.draw.rect(minimap_bg, ROCK_COLOR, rect)
        elif val == 5: pygame.draw.rect(minimap_bg, WATER_COLOR, rect)
        elif val == 6: pygame.draw.rect(minimap_bg, DIRT_COLOR, rect)

fog_surface = pygame.Surface((WIDTH, HEIGHT))
clock = pygame.time.Clock()
running = True

while running:
    mouse_x, mouse_y = pygame.mouse.get_pos()
    VIEW_HEIGHT = HEIGHT - TOP_BAR_HEIGHT - UI_HEIGHT
    BOTTOM_UI_Y = HEIGHT - UI_HEIGHT
    v_width, v_height = WIDTH / zoom, VIEW_HEIGHT / zoom
    
    minimap_rect = pygame.Rect(20, BOTTOM_UI_Y + 10, MINIMAP_SIZE, MINIMAP_SIZE)
    if pygame.mouse.get_pressed()[0] and minimap_rect.collidepoint(mouse_x, mouse_y):
        camera_x = ((mouse_x - 20) / MINIMAP_SIZE) * WORLD_WIDTH - (v_width / 2)
        camera_y = ((mouse_y - (BOTTOM_UI_Y + 10)) / MINIMAP_SIZE) * WORLD_HEIGHT - (v_height / 2)

    world_mouse_x = (mouse_x / zoom) + camera_x
    world_mouse_y = ((mouse_y - TOP_BAR_HEIGHT) / zoom) + camera_y

    current_pop = len(units)
    max_pop = 5 + (sum(1 for b in buildings if b.is_built and b.b_type in ['house', 'base']) * 5)
    
    global_time += 1
    new_day = (global_time // DAY_LENGTH_FRAMES) + 1
    if new_day > current_day: current_day = new_day; horde_spawned = False 
        
    time_ratio = (global_time % DAY_LENGTH_FRAMES) / DAY_LENGTH_FRAMES
    hour, minutes = int(time_ratio * 24), int((time_ratio * 24 % 1) * 60)
    time_str = f"Dzień {current_day} - {hour:02d}:{minutes:02d}"
    
    phase_name, vision_mod, night_alpha, is_night = "Dzień", 1.0, 50, False
    if 18 <= hour < 20: phase_name, vision_mod, night_alpha = "Zmierzch", 1.0 - ((hour - 18 + minutes/60) / 2 * 0.5), int(50 + ((hour - 18 + minutes/60) / 2) * 150)
    elif 20 <= hour or hour < 4: phase_name, vision_mod, night_alpha, is_night = "Noc", 0.5, 200, True
    elif 4 <= hour < 6: phase_name, vision_mod, night_alpha = "Świt", 0.5 + ((hour - 4 + minutes/60) / 2 * 0.5), int(200 - ((hour - 4 + minutes/60) / 2) * 150)

    if phase_name == "Noc":
        if current_day == horde_day and hour == 20 and not horde_spawned:
            show_message(f"Horda Zombie atakuje! ({horde_size} zainfekowanych)")
            for _ in range(horde_size):
                zx, zy = get_zombie_spawn_point(buildings, WORLD_WIDTH, WORLD_HEIGHT)
                if zx: zombies.append(Zombie(zx, zy))
            horde_spawned = True
        if random.random() < (0.004 + (current_day * 0.002)): 
            zx, zy = get_zombie_spawn_point(buildings, WORLD_WIDTH, WORLD_HEIGHT)
            if zx: zombies.append(Zombie(zx, zy))

    if global_message_timer > 0: global_message_timer -= 1

    active_buttons = []
    selected_workers = sum(1 for u in units if u.is_selected and u.u_type == 'worker')
    selected_bases = [b for b in buildings if b.is_selected and b.b_type == 'base' and b.is_built]
    selected_barracks = [b for b in buildings if b.is_selected and b.b_type == 'barracks' and b.is_built]
    
    if selected_bases:
        w_cost = UNIT_STATS['worker']
        active_buttons.append({'id': 'R_WORKER', 'label': 'Robotnik', 'w': w_cost['cost_wood'], 'c': w_cost['cost_crystal'], 'hotkey': 'R', 'col': 0, 'row': 0})
        if selected_bases[0].recruit_queue > 0: active_buttons.append({'id': 'CANCEL_B', 'label': 'Anuluj', 'w': 0, 'c': 0, 'hotkey': 'Esc', 'col': 1, 'row': 0})
    elif selected_barracks:
        a_cost = UNIT_STATS['archer']
        active_buttons.append({'id': 'R_ARCHER', 'label': 'Łucznik', 'w': a_cost['cost_wood'], 'c': a_cost['cost_crystal'], 'hotkey': 'A', 'col': 0, 'row': 0})
        if selected_barracks[0].recruit_queue > 0: active_buttons.append({'id': 'CANCEL_B', 'label': 'Anuluj', 'w': 0, 'c': 0, 'hotkey': 'Esc', 'col': 1, 'row': 0})
    elif selected_workers > 0:
        active_buttons.append({'id': 'B_HOUSE', 'label': 'Domek', 'w': COSTS['house'][0], 'c': COSTS['house'][1], 'hotkey': 'H', 'col': 0, 'row': 0})
        active_buttons.append({'id': 'B_BARRACKS', 'label': 'Baraki', 'w': COSTS['barracks'][0], 'c': COSTS['barracks'][1], 'hotkey': 'B', 'col': 1, 'row': 0})
        active_buttons.append({'id': 'B_WALL', 'label': 'Mur', 'w': COSTS['wall'][0], 'c': COSTS['wall'][1], 'hotkey': 'W', 'col': 2, 'row': 0})
        active_buttons.append({'id': 'B_BASE', 'label': 'Baza', 'w': COSTS['base'][0], 'c': COSTS['base'][1], 'hotkey': 'Q', 'col': 3, 'row': 0})
        active_buttons.append({'id': 'B_TOWER', 'label': 'Wieża', 'w': COSTS['tower'][0], 'c': COSTS['tower'][1], 'hotkey': 'T', 'col': 4, 'row': 0})

    cmd_card_start_x, cmd_card_start_y = WIDTH - 500, BOTTOM_UI_Y + 30
    for btn in active_buttons: btn['rect'] = pygame.Rect(cmd_card_start_x + (btn['col'] * 90), cmd_card_start_y + (btn['row'] * 60), 80, 50)

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        elif event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            VIEW_HEIGHT = HEIGHT - TOP_BAR_HEIGHT - UI_HEIGHT
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            fog_surface = pygame.Surface((WIDTH, HEIGHT)) 
            
        elif event.type == pygame.MOUSEWHEEL:
            if pending_command == 'BUILD_wall': wall_rotation = 1 - wall_rotation 
            else: zoom = max(0.5, min(zoom + event.y * 0.1, 2.0))
                
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                for u in units:
                    if u.is_selected: u.command_stop()
                pending_command = None
            elif event.key == pygame.K_m: pending_command = 'MOVE'
            elif event.key == pygame.K_a: pending_command = 'ATTACK'
            elif selected_workers > 0:
                if event.key == pygame.K_h: pending_command = 'BUILD_house'
                elif event.key == pygame.K_b: pending_command = 'BUILD_barracks'
                elif event.key == pygame.K_w: pending_command = 'BUILD_wall'
                elif event.key == pygame.K_q: pending_command = 'BUILD_base'
                elif event.key == pygame.K_t: pending_command = 'BUILD_tower'
            elif event.key == pygame.K_r and selected_bases:
                w_cost = UNIT_STATS['worker']
                if current_pop + selected_bases[0].recruit_queue >= max_pop: show_message("Limit Populacji!")
                elif res['wood'] >= w_cost['cost_wood']: res['wood'] -= w_cost['cost_wood']; selected_bases[0].recruit_queue += 1
            elif event.key == pygame.K_a and selected_barracks:
                a_cost = UNIT_STATS['archer']
                if current_pop + selected_barracks[0].recruit_queue >= max_pop: show_message("Limit Populacji!")
                elif res['wood'] >= a_cost['cost_wood'] and res['crystals'] >= a_cost['cost_crystal']: 
                    res['wood'] -= a_cost['cost_wood']; res['crystals'] -= a_cost['cost_crystal']; selected_barracks[0].recruit_queue += 1
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if minimap_rect.collidepoint(mouse_x, mouse_y) or mouse_y < TOP_BAR_HEIGHT: continue
                elif mouse_y >= BOTTOM_UI_Y:
                    clicked_ui = False
                    for btn in active_buttons:
                        if btn['rect'].collidepoint(mouse_x, mouse_y):
                            clicked_ui = True
                            if btn['id'] == 'R_WORKER' and selected_bases:
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
                            elif btn['id'].startswith('B_'): pending_command = 'BUILD_' + btn['id'].split('_')[1].lower()
                    if not clicked_ui: pending_command = None
                
                else:
                    if pending_command in ['MOVE', 'ATTACK']:
                        target_entity = None
                        if pending_command == 'ATTACK':
                            target_entity = next((z for z in reversed(zombies) if math.hypot(z.x - world_mouse_x, z.y - world_mouse_y) <= z.radius), None)
                            if not target_entity: target_entity = next((u for u in reversed(units) if math.hypot(u.x - world_mouse_x, u.y - world_mouse_y) <= u.radius), None)
                            if not target_entity: target_entity = next((b for b in buildings if b.rect.collidepoint(world_mouse_x, world_mouse_y)), None)
                        for u in units:
                            if u.is_selected:
                                if pending_command == 'ATTACK' and target_entity: u.command_attack(target_entity)
                                else: u.command_move(world_mouse_x, world_mouse_y)
                        pending_command = None; continue
                        
                    elif pending_command and pending_command.startswith('BUILD_'):
                        b_type = pending_command.split('_')[1]
                        cost_w, cost_c = COSTS[b_type]
                        if not is_obstacle(world_mouse_x, world_mouse_y):
                            rad = 15 if b_type == 'wall' else (35 if b_type == 'barracks' else (45 if b_type == 'base' else 25))
                            collision_rect = pygame.Rect(world_mouse_x - rad, world_mouse_y - rad, rad*2, rad*2)
                            if not any(b.rect.colliderect(collision_rect) for b in buildings):
                                if res['wood'] >= cost_w and res['crystals'] >= cost_c:
                                    res['wood'] -= cost_w; res['crystals'] -= cost_c
                                    for u in units:
                                        if u.is_selected and u.u_type == 'worker': u.command_build(world_mouse_x, world_mouse_y, b_type, wall_rotation)
                                else: show_message("Brak surowców na budowę!")
                        if b_type != 'wall': pending_command = None 
                        continue

                    current_time = pygame.time.get_ticks()
                    clicked_u = next((u for u in reversed(units) if math.hypot(u.x - world_mouse_x, u.y - world_mouse_y) <= u.radius), None)
                    clicked_b = next((b for b in buildings if b.rect.collidepoint(world_mouse_x, world_mouse_y)), None)
                    clicked_c = next((c for c in crystals if math.hypot(c.x - world_mouse_x, c.y - world_mouse_y) <= c.radius), None)
                    clicked_t = next((t for t in trees if math.hypot(t.x - world_mouse_x, t.y - world_mouse_y) <= t.radius), None)

                    if clicked_u:
                        if current_time - last_click_time < 300 and last_clicked_type == clicked_u.title:
                            for u in units: u.is_selected = False
                            for u in units:
                                if u.title == clicked_u.title and math.hypot(u.x - clicked_u.x, u.y - clicked_u.y) < 400: u.is_selected = True
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
            
            elif event.button == 3: 
                if TOP_BAR_HEIGHT <= mouse_y < BOTTOM_UI_Y:
                    pending_command = None
                    if selected_bases: selected_bases[0].rally_x, selected_bases[0].rally_y = world_mouse_x, world_mouse_y
                    elif selected_barracks: selected_barracks[0].rally_x, selected_barracks[0].rally_y = world_mouse_x, world_mouse_y
                    else:
                        clicked_res = next((t for t in trees if math.hypot(t.x - world_mouse_x, t.y - world_mouse_y) <= t.radius), None)
                        if not clicked_res: clicked_res = next((c for c in crystals if math.hypot(c.x - world_mouse_x, c.y - world_mouse_y) <= c.radius), None)
                        clicked_enemy = next((z for z in reversed(zombies) if math.hypot(z.x - world_mouse_x, z.y - world_mouse_y) <= z.radius), None)
                        
                        for u in units:
                            if u.is_selected:
                                if clicked_enemy: u.command_attack(clicked_enemy)
                                elif clicked_res and u.u_type == 'worker': u.command_harvest(clicked_res)
                                elif not is_obstacle(world_mouse_x, world_mouse_y): u.command_move(world_mouse_x, world_mouse_y)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and is_selecting:
                is_selecting = False
                w, h = abs(selection_start_world[0] - world_mouse_x), abs(selection_start_world[1] - world_mouse_y)
                rect = pygame.Rect(min(selection_start_world[0], world_mouse_x), min(selection_start_world[1], world_mouse_y), w, h)
                for u in units:
                    if rect.collidepoint(u.x, u.y): u.is_selected = True

    if mouse_x < SCROLL_MARGIN: camera_x -= CAMERA_SPEED
    elif mouse_x > WIDTH - SCROLL_MARGIN: camera_x += CAMERA_SPEED
    if mouse_y < SCROLL_MARGIN: camera_y -= CAMERA_SPEED
    elif mouse_y > HEIGHT - SCROLL_MARGIN: camera_y += CAMERA_SPEED
    
    camera_x = max(-OOB_MARGIN, min(camera_x, WORLD_WIDTH - v_width + OOB_MARGIN))
    camera_y = max(-OOB_MARGIN, min(camera_y, WORLD_HEIGHT - v_height + OOB_MARGIN))

    for b in buildings:
        result = b.update(zombies, visual_effects, is_night)
        if result == 'spawn_worker':
            u = Unit(b.x + 60, b.y + 60, 'worker'); u.command_move(b.rally_x, b.rally_y); units.append(u)
        elif result == 'spawn_archer':
            u = Unit(b.x + 60, b.y + 60, 'archer'); u.command_move(b.rally_x, b.rally_y); units.append(u)
        elif result == 'spawn_zombie': zombies.append(Zombie(b.x, b.y + 40))

    for u in units: u.update(res, buildings, trees, crystals, zombies, is_obstacle, get_speed_mod, visual_effects)
    for z in zombies: z.update(units, buildings, is_obstacle, get_speed_mod, visual_effects)
    
    for ef in visual_effects: ef['timer'] -= 1
    visual_effects = [ef for ef in visual_effects if ef['timer'] > 0]
    
    resolve_collisions(units, buildings, is_obstacle)
    resolve_collisions(zombies, buildings, is_obstacle)
    
    trees = [t for t in trees if t.hp > 0]; crystals = [c for c in crystals if c.hp > 0]
    units = [u for u in units if u.hp > 0]; buildings = [b for b in buildings if b.hp > 0]
    zombies = [z for z in zombies if z.hp > 0]

    # --- RENDER ŚWIATA ---
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
        if is_visible(b, camera_x, camera_y, v_width, v_height): b.draw(world_surface, camera_x, camera_y)
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
        if is_visible(u, camera_x, camera_y, v_width, v_height): u.draw(world_surface, camera_x, camera_y)
    for z in zombies:
        if is_visible(z, camera_x, camera_y, v_width, v_height): z.draw(world_surface, camera_x, camera_y)
        
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
    elif pending_command and pending_command.startswith('BUILD_'):
        b_type = pending_command.split('_')[1]
        mx, my = world_mouse_x - camera_x, world_mouse_y - camera_y
        can_build = not is_obstacle(world_mouse_x, world_mouse_y)
        rad = 15 if b_type == 'wall' else (35 if b_type == 'barracks' else (45 if b_type == 'base' else 25))
        check_rect = pygame.Rect(world_mouse_x - rad, world_mouse_y - rad, rad*2, rad*2)
        if any(b.rect.colliderect(check_rect) for b in buildings): can_build = False
        grid_color = (0, 255, 0, 100) if can_build else (255, 0, 0, 100)
        
        if b_type == 'wall':
            w, h = (60, 20) if wall_rotation == 0 else (20, 60)
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            s.fill(grid_color)
            pygame.draw.rect(s, (255, 255, 255, 120), (0, 0, w, h), 1)
            world_surface.blit(s, (mx - w//2, my - h//2))
        else:
            s = pygame.Surface((rad*2, rad*2), pygame.SRCALPHA)
            s.fill(grid_color)
            for i in range(0, rad*2, 10):
                pygame.draw.line(s, (255,255,255,40), (i, 0), (i, rad*2))
                pygame.draw.line(s, (255,255,255,40), (0, i), (rad*2, i))
            pygame.draw.circle(s, (255, 255, 255, 180), (rad, rad), rad, 2)
            world_surface.blit(s, (mx - rad, my - rad))

    if fog_surface.get_size() != (int(v_width), int(v_height)):
        fog_surface = pygame.Surface((int(v_width), int(v_height)))
    fog_surface.fill(NIGHT_COLOR)
    
    for u in units: pygame.draw.circle(fog_surface, MAGENTA, (int(u.x - camera_x), int(u.y - camera_y)), int(u.vision_range * vision_mod))
    for b in buildings: 
        if b.is_built: pygame.draw.circle(fog_surface, MAGENTA, (int(b.x - camera_x), int(b.y - camera_y)), int(b.vision_range * vision_mod))
    
    fog_surface.set_colorkey(MAGENTA)
    fog_surface.set_alpha(night_alpha)
    world_surface.blit(fog_surface, (0, 0))

    scaled_world = pygame.transform.scale(world_surface, (WIDTH, VIEW_HEIGHT))
    screen.blit(scaled_world, (0, TOP_BAR_HEIGHT)) 
    if global_message_timer > 0:
        msg_surf = font_bold.render(global_message, True, RED)
        screen.blit(msg_surf, ((WIDTH - msg_surf.get_width()) // 2, TOP_BAR_HEIGHT + 20))

    # --- INTERFEJS ---
    pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, TOP_BAR_HEIGHT))
    pygame.draw.line(screen, UI_BORDER, (0, TOP_BAR_HEIGHT), (WIDTH, TOP_BAR_HEIGHT), 2)
    screen.blit(font_bold.render(f"{time_str} | {phase_name}", True, YELLOW if phase_name == "Dzień" else CYAN), (20, 5))
    draw_resource_icon(screen, WIDTH - 420, 15, 'wood'); screen.blit(font_main.render(str(res['wood']), True, WHITE), (WIDTH - 405, 5))
    draw_resource_icon(screen, WIDTH - 300, 15, 'crystal'); screen.blit(font_main.render(str(res['crystals']), True, WHITE), (WIDTH - 285, 5))
    screen.blit(font_main.render(f"Pop: {current_pop}/{max_pop}", True, RED if current_pop >= max_pop else WHITE), (WIDTH - 150, 5))

    pygame.draw.rect(screen, DARK_GRAY, (0, BOTTOM_UI_Y, WIDTH, UI_HEIGHT))
    pygame.draw.line(screen, UI_BORDER, (0, BOTTOM_UI_Y), (WIDTH, BOTTOM_UI_Y), 4)

    screen.blit(minimap_bg, (20, BOTTOM_UI_Y + 10))
    for u in units: pygame.draw.rect(screen, BLUE, (20 + int(u.x * SCALE_X), BOTTOM_UI_Y + 10 + int(u.y * SCALE_Y), 2, 2))
    for z in zombies: pygame.draw.rect(screen, RED, (20 + int(z.x * SCALE_X), BOTTOM_UI_Y + 10 + int(z.y * SCALE_Y), 2, 2))
    pygame.draw.rect(screen, WHITE, (20 + int(camera_x * SCALE_X), BOTTOM_UI_Y + 10 + int(camera_y * SCALE_Y), int(v_width * SCALE_X), int(v_height * SCALE_Y)), 1)
    pygame.draw.line(screen, UI_BORDER, (180, BOTTOM_UI_Y), (180, HEIGHT), 2)

    info_x = 200
    if selected_bases:
        target = selected_bases[0]
        screen.blit(font_bold.render(target.title, True, WHITE), (info_x, BOTTOM_UI_Y + 20))
        screen.blit(font_small.render(f"HP: {target.hp} / {target.max_hp}", True, RED), (info_x, BOTTOM_UI_Y + 50))
        if target.recruit_queue > 0:
            screen.blit(font_main.render(f"Produkcja: Robotnik ({target.recruit_queue})", True, LIGHT_GRAY), (info_x, BOTTOM_UI_Y + 70))
            pygame.draw.rect(screen, DARK_GRAY, (info_x, BOTTOM_UI_Y + 100, 160, 12))
            pygame.draw.rect(screen, GREEN, (info_x, BOTTOM_UI_Y + 100, int(160 * (target.recruit_progress / target.recruit_time_max)), 12))
    elif selected_barracks:
        target = selected_barracks[0]
        screen.blit(font_bold.render(target.title, True, WHITE), (info_x, BOTTOM_UI_Y + 20))
        screen.blit(font_small.render(f"HP: {target.hp} / {target.max_hp}", True, RED), (info_x, BOTTOM_UI_Y + 50))
        if target.recruit_queue > 0:
            screen.blit(font_main.render(f"Produkcja: Łucznik ({target.recruit_queue})", True, LIGHT_GRAY), (info_x, BOTTOM_UI_Y + 70))
            pygame.draw.rect(screen, DARK_GRAY, (info_x, BOTTOM_UI_Y + 100, 160, 12))
            pygame.draw.rect(screen, GREEN, (info_x, BOTTOM_UI_Y + 100, int(160 * (target.recruit_progress / target.recruit_time_max)), 12))
    else:
        selected_buildings = [b for b in buildings if b.is_selected]
        selected_zombies = [z for z in zombies if z.is_selected]
        if len(selected_buildings) > 0:
            target = selected_buildings[0]
            screen.blit(font_bold.render(target.title, True, WHITE), (info_x, BOTTOM_UI_Y + 20))
            screen.blit(font_small.render(f"HP: {target.hp} / {target.max_hp}", True, RED), (info_x, BOTTOM_UI_Y + 50))
            bonus = "+5 Populacji" if target.b_type == 'house' else ("Gniazdo potworów" if target.b_type == 'cemetery' else "Struktura gracza")
            screen.blit(font_main.render(bonus if target.is_built else "W budowie...", True, LIGHT_GRAY), (info_x, BOTTOM_UI_Y + 70))
        elif len(selected_zombies) > 0:
            target = selected_zombies[0]
            screen.blit(font_bold.render(target.title, True, (255, 100, 100)), (info_x, BOTTOM_UI_Y + 20))
            screen.blit(font_small.render(f"HP: {target.hp} / {target.max_hp} | Dmg: {target.damage}", True, RED), (info_x, BOTTOM_UI_Y + 50))
        else:
            selected_crystals = [c for c in crystals if c.is_selected]
            selected_trees = [t for t in trees if t.is_selected]
            if len(selected_crystals) > 0:
                target = selected_crystals[0]
                screen.blit(font_bold.render(target.title, True, CYAN), (info_x, BOTTOM_UI_Y + 20))
                screen.blit(font_main.render(f"Zasoby: {target.amount} / {target.max_amount}", True, WHITE), (info_x, BOTTOM_UI_Y + 50))
            elif len(selected_trees) > 0:
                target = selected_trees[0]
                screen.blit(font_bold.render(target.title, True, GREEN), (info_x, BOTTOM_UI_Y + 20))
                screen.blit(font_main.render(f"Zasoby: {target.amount} / {target.max_amount}", True, WHITE), (info_x, BOTTOM_UI_Y + 50))
            elif len([u for u in units if u.is_selected]) > 0:
                count = len([u for u in units if u.is_selected])
                screen.blit(font_bold.render(f"Zaznaczone jednostki ({count})", True, WHITE), (info_x, BOTTOM_UI_Y + 20))
                su = next((u for u in units if u.is_selected), None)
                if su: screen.blit(font_small.render(f"HP: {su.hp}/{su.max_hp} | Atak DMG: {su.damage}", True, RED), (info_x, BOTTOM_UI_Y + 50))

    pygame.draw.line(screen, UI_BORDER, (cmd_card_start_x - 20, BOTTOM_UI_Y), (cmd_card_start_x - 20, HEIGHT), 2)
    pygame.draw.rect(screen, (20, 25, 30), (cmd_card_start_x - 20, BOTTOM_UI_Y, WIDTH, UI_HEIGHT)) 

    for btn in active_buttons:
        pygame.draw.rect(screen, (50, 60, 80), btn['rect'])
        pygame.draw.rect(screen, UI_BORDER, btn['rect'], 2)
        text_surf = font_main.render(btn['label'], True, WHITE)
        screen.blit(text_surf, (btn['rect'].x + (btn['rect'].width - text_surf.get_width()) // 2, btn['rect'].y + 5))
        
        if btn['w'] > 0 or btn['c'] > 0:
            cx, cy = btn['rect'].x + 5, btn['rect'].y + 35
            if btn['w'] > 0:
                draw_resource_icon(screen, cx, cy, 'wood'); wsurf = font_small.render(str(btn['w']), True, WHITE)
                screen.blit(wsurf, (cx + 10, cy - 6)); cx += wsurf.get_width() + 20
            if btn['c'] > 0:
                draw_resource_icon(screen, cx, cy, 'crystal'); csurf = font_small.render(str(btn['c']), True, WHITE)
                screen.blit(csurf, (cx + 10, cy - 6))
            
        screen.blit(font_small.render(btn['hotkey'], True, LIGHT_GRAY), (btn['rect'].x + 2, btn['rect'].y + 2))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()