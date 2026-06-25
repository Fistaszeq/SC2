import math
import random
import pygame
from config import *
from pathfinding import get_astar_path

def draw_hp_bar(surface, x, y, hp, max_hp, width=30):
    if hp < max_hp or hp <= 0:
        bx, by = x - width // 2, y - 20
        pygame.draw.rect(surface, RED, (bx, by, width, 4))
        pygame.draw.rect(surface, GREEN, (bx, by, int(width * (max(0, hp) / max_hp)), 4))

class Tree:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.radius = random.randint(12, 28)
        self.amount = self.max_amount = self.radius * 20 
        self.hp = self.max_hp = self.amount
        self.max_workers = max(1, self.radius // 6) # Dynamiczny limit robotników
        self.is_selected, self.type, self.title = False, 'wood', "Złoże Drewna"
        self.color = (random.randint(20, 40), random.randint(100, 150), random.randint(20, 40))
    def draw_hp(self, surface, cam_x, cam_y):
        if self.hp < self.max_hp: draw_hp_bar(surface, int(self.x - cam_x), int(self.y - cam_y), self.hp, self.max_hp)

class Crystal:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.radius = random.randint(10, 20)
        self.amount = self.max_amount = self.radius * 25 
        self.hp = self.max_hp = self.amount
        self.max_workers = max(1, self.radius // 5) 
        self.is_selected, self.type, self.title = False, 'crystal', "Złoże Kryształów"
        self.color = CYAN
    def draw_hp(self, surface, cam_x, cam_y):
        if self.hp < self.max_hp: draw_hp_bar(surface, int(self.x - cam_x), int(self.y - cam_y), self.hp, self.max_hp)

def get_available_resource(unit, res_list, all_units):
    """Zwraca najbliższy surowiec, który ma jeszcze wolne sloty na pracowników."""
    counts = {r: 0 for r in res_list}
    for u in all_units:
        if getattr(u, 'target_obj', None) in counts and u.state in ['MOVE', 'HARVEST', 'SEARCH_MOVE']:
            counts[u.target_obj] += 1
            
    best, min_d_sq = None, float('inf')
    for r in res_list:
        if counts[r] < r.max_workers:
            d_sq = (r.x - unit.x)**2 + (r.y - unit.y)**2
            if d_sq < min_d_sq: best, min_d_sq = r, d_sq
    return best

class Building:
    def __init__(self, col, row, b_type):
        self.col, self.row, self.b_type = int(col), int(row), b_type
        self.is_selected, self.is_built, self.build_progress = False, False, 0
        
        st = BUILDING_STATS[b_type]
        self.title, self.color = st['title'], st['color']
        self.max_hp = st['hp']
        self.hp = 1
        self.build_max = st['build_time']
        self.w_tiles, self.h_tiles = st['w_tiles'], st['h_tiles']
        
        self.rect = pygame.Rect(self.col * TILE_SIZE, self.row * TILE_SIZE, self.w_tiles * TILE_SIZE, self.h_tiles * TILE_SIZE)
        self.x, self.y = self.rect.centerx, self.rect.centery
        self.radius = (max(self.rect.width, self.rect.height) // 2) + 5
        
        self.vision_range = 150 if b_type != 'base' else 400
        self.recruit_queue, self.recruit_progress, self.recruit_time_max = 0, 0, (240 if b_type == 'barracks' else 180)
        self.attack_timer, self.spawn_timer = 0, 0
        self.rally_x, self.rally_y = self.x + 80, self.y + 80
        
        # Mechaniki wieżyczek
        self.turret_angle = 0
        self.garrisoned_unit = None
        
        if b_type == 'tower': self.vision_range, self.damage, self.attack_cooldown = 300, 15, 60
        elif b_type == 'double_tower': self.vision_range, self.damage, self.attack_cooldown = 350, 20, 40
        elif b_type == 'obs_tower': self.vision_range = 250
        elif b_type == 'cemetery': self.is_built, self.hp = True, self.max_hp

    def update(self, enemies_list, effects_list, is_night=False, vision_mask=None):
        if not self.is_built:
            self.build_progress += 1
            self.hp = max(1, int(self.max_hp * (self.build_progress / self.build_max)))
            if self.build_progress >= self.build_max: self.is_built = True
        else:
            # Wieża Obserwacyjna - mechanika widzenia
            if self.b_type == 'obs_tower':
                if self.garrisoned_unit:
                    self.vision_range = 600
                    if self.garrisoned_unit.u_type == 'archer':
                        if self.attack_timer > 0: self.attack_timer -= 1
                        elif enemies_list:
                            for e in enemies_list:
                                dx, dy = e.x - self.x, e.y - self.y
                                if (dx*dx + dy*dy) <= (450 * 450): # Mega zasięg z wieży
                                    e.hp -= self.garrisoned_unit.damage * 1.5
                                    effects_list.append({'x1': self.x, 'y1': self.y - 20, 'x2': e.x, 'y2': e.y, 'timer': 8, 'color': WHITE})
                                    self.attack_timer = self.garrisoned_unit.attack_cooldown 
                                    break
                else:
                    self.vision_range = 250

            if self.b_type in ['base', 'barracks']:
                if self.recruit_queue > 0:
                    self.recruit_progress += 1
                    if self.recruit_progress >= self.recruit_time_max:
                        self.recruit_progress, self.recruit_queue = 0, self.recruit_queue - 1
                        return 'spawn_worker' if self.b_type == 'base' else 'spawn_archer'
                else: self.recruit_progress = 0
            
            # WIEŻYCZKI: Mogą strzelać tylko w to co widzą (is_in_vision opiera się o dystans i mgłę w main.py, ale uprośćmy: muszą być w vision_range)
            if self.b_type in ['tower', 'double_tower']:
                if self.attack_timer > 0: self.attack_timer -= 1
                
                target = None
                min_d = self.vision_range * self.vision_range
                for e in enemies_list:
                    dx, dy = e.x - self.x, e.y - self.y
                    d_sq = dx*dx + dy*dy
                    if d_sq <= min_d: target, min_d = e, d_sq
                        
                if target:
                    # Obrót lufy
                    self.turret_angle = math.atan2(target.y - self.y, target.x - self.x)
                    if self.attack_timer <= 0:
                        target.hp -= self.damage
                        if self.b_type == 'double_tower':
                            # Wizualizacja dwóch strzałów
                            ox, oy = math.cos(self.turret_angle + 1.57)*5, math.sin(self.turret_angle + 1.57)*5
                            effects_list.append({'x1': self.x+ox, 'y1': self.y+oy, 'x2': target.x, 'y2': target.y, 'timer': 8, 'color': YELLOW})
                            effects_list.append({'x1': self.x-ox, 'y1': self.y-oy, 'x2': target.x, 'y2': target.y, 'timer': 8, 'color': YELLOW})
                        else:
                            effects_list.append({'x1': self.x, 'y1': self.y, 'x2': target.x, 'y2': target.y, 'timer': 8, 'color': YELLOW})
                        self.attack_timer = self.attack_cooldown 
                            
            if self.b_type == 'cemetery':
                if is_night:
                    self.spawn_timer += 1
                    if self.spawn_timer >= 240:
                        self.spawn_timer, self.hp = 0, min(self.max_hp, self.hp + 50)
                        return 'spawn_zombie'
                else: self.spawn_timer = 0
        return None

    def draw(self, surface, cam_x, cam_y):
        draw_rect = self.rect.move(-cam_x, -cam_y)
        cx, cy = draw_rect.centerx, draw_rect.centery
        
        if not self.is_built:
            pygame.draw.rect(surface, (150, 100, 0), draw_rect, 2)
            pygame.draw.rect(surface, GREEN, (draw_rect.x, draw_rect.y - 15, int(draw_rect.width * (self.build_progress / self.build_max)), 6))
        else:
            pygame.draw.rect(surface, self.color, draw_rect)
            
            if self.b_type == 'cemetery': pygame.draw.rect(surface, (20, 20, 20), (cx - 10, cy - 20, 20, 40)) 
            elif self.b_type == 'workshop': pygame.draw.circle(surface, DARK_GRAY, (cx, cy), 15)
            elif self.b_type == 'obs_tower':
                pygame.draw.circle(surface, (50, 50, 50), (cx, cy), 15)
                if self.garrisoned_unit:
                    u_col = BLUE if self.garrisoned_unit.u_type == 'worker' else (150, 200, 150)
                    pygame.draw.circle(surface, u_col, (cx, cy), 8) # Widoczna jednostka wewnątrz
                    
            elif self.b_type == 'tower':
                pygame.draw.circle(surface, DARK_GRAY, (cx, cy), 12)
                end_x = cx + math.cos(self.turret_angle) * 18
                end_y = cy + math.sin(self.turret_angle) * 18
                pygame.draw.line(surface, BLACK, (cx, cy), (end_x, end_y), 4)
            elif self.b_type == 'double_tower':
                pygame.draw.circle(surface, DARK_GRAY, (cx, cy), 16)
                ox, oy = math.cos(self.turret_angle + 1.57)*5, math.sin(self.turret_angle + 1.57)*5
                dx, dy = math.cos(self.turret_angle)*22, math.sin(self.turret_angle)*22
                pygame.draw.line(surface, BLACK, (cx+ox, cy+oy), (cx+ox+dx, cy+oy+dy), 3)
                pygame.draw.line(surface, BLACK, (cx-ox, cy-oy), (cx-ox+dx, cy-oy+dy), 3)
                
            if self.b_type in ['tower', 'double_tower', 'obs_tower'] and self.is_selected:
                vr = 450 if self.b_type == 'obs_tower' and getattr(self.garrisoned_unit, 'u_type', '') == 'archer' else self.vision_range
                s = pygame.Surface((vr*2, vr*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 0, 0, 50) if self.b_type != 'obs_tower' else (0, 255, 0, 50), (vr, vr), vr)
                surface.blit(s, (cx - vr, cy - vr))
                
        if self.is_selected: pygame.draw.rect(surface, WHITE, draw_rect, 2)
        
        if self.b_type in ['base', 'barracks'] and self.is_built and self.is_selected:
            rx, ry = int(self.rally_x - cam_x), int(self.rally_y - cam_y)
            pygame.draw.line(surface, WHITE, (cx, cy), (rx, ry), 1)
            pygame.draw.circle(surface, GREEN, (rx, ry), 5)
            
        draw_hp_bar(surface, cx, cy, self.hp, self.max_hp)

class Unit:
    def __init__(self, x, y, u_type='worker'):
        self.x, self.y, self.u_type = x, y, u_type
        self.is_selected, self.state = False, 'IDLE'
        self.target_obj, self.target_x, self.target_y = None, x, y
        self.carry_type, self.carry_amount, self.harvest_timer = None, 0, 0
        self.last_harvest_x, self.last_harvest_y, self.search_type = x, y, None
        
        self.path = [] 
        self.is_hidden, self.building_ref = False, None
        
        st = UNIT_STATS[u_type]
        self.title, self.speed, self.radius = st['title'], st['speed'], (12 if u_type == 'worker' else 10)
        self.hp = self.max_hp = st['hp']
        self.vision_range, self.damage = st['vision'], st['damage']
        self.attack_range, self.attack_cooldown = st['range'], st['cooldown']
        self.color = BLUE if u_type == 'worker' else (150, 200, 150)
        self.attack_timer = 0

    def calculate_path(self, tx, ty, game_map, MAP_COLS, MAP_ROWS, buildings_list):
        self.path = get_astar_path((self.x//TILE_SIZE, self.y//TILE_SIZE), (tx//TILE_SIZE, ty//TILE_SIZE), game_map, MAP_COLS, MAP_ROWS, buildings_list)
        self.target_x, self.target_y = tx, ty

    def command_move(self, tx, ty, game_map, MAP_COLS, MAP_ROWS, buildings_list): 
        self.state, self.target_obj, self.is_hidden, self.building_ref = 'MOVE', None, False, None
        self.calculate_path(tx, ty, game_map, MAP_COLS, MAP_ROWS, buildings_list)

    def command_harvest(self, resource_obj, game_map, MAP_COLS, MAP_ROWS, buildings_list): 
        self.state, self.target_obj, self.is_hidden, self.building_ref = 'HARVEST', resource_obj, False, None
        self.calculate_path(resource_obj.x, resource_obj.y, game_map, MAP_COLS, MAP_ROWS, buildings_list)

    def command_attack(self, obj, game_map, MAP_COLS, MAP_ROWS, buildings_list): 
        self.state, self.target_obj, self.is_hidden, self.building_ref = 'ATTACK', obj, False, None
        self.calculate_path(obj.x, obj.y, game_map, MAP_COLS, MAP_ROWS, buildings_list)

    def command_build(self, t_col, t_row, b_type, game_map, MAP_COLS, MAP_ROWS, buildings_list): 
        self.state, self.target_obj, self.is_hidden, self.building_ref = 'BUILD', {'type': b_type, 'col': t_col, 'row': t_row}, False, None
        tx = (t_col * TILE_SIZE) + (BUILDING_STATS[b_type]['w_tiles'] * TILE_SIZE) // 2
        ty = (t_row * TILE_SIZE) + (BUILDING_STATS[b_type]['h_tiles'] * TILE_SIZE) // 2
        self.calculate_path(tx, ty, game_map, MAP_COLS, MAP_ROWS, buildings_list)
        
    def command_garrison(self, tower_obj, game_map, MAP_COLS, MAP_ROWS, buildings_list):
        self.state, self.target_obj = 'GARRISON', tower_obj
        self.calculate_path(tower_obj.x, tower_obj.y, game_map, MAP_COLS, MAP_ROWS, buildings_list)

    def command_stop(self): 
        self.state, self.target_obj, self.target_x, self.target_y, self.path, self.is_hidden, self.building_ref = 'IDLE', None, self.x, self.y, [], False, None

    def get_closest_base(self, buildings_list):
        bases = [b for b in buildings_list if b.b_type == 'base' and b.is_built and b.hp > 0]
        return min(bases, key=lambda b: (b.x - self.x)**2 + (b.y - self.y)**2) if bases else None

    def _follow_path(self, buildings_list, is_obstacle_fn, get_speed_mod):
        if not self.path:
            dx, dy = self.target_x - self.x, self.target_y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                s = self.speed * get_speed_mod(self.x, self.y)
                if not is_obstacle_fn(self.x + (dx/dist)*s, self.y): self.x += (dx/dist)*s
                if not is_obstacle_fn(self.x, self.y + (dy/dist)*s): self.y += (dy/dist)*s
            return
            
        next_x, next_y = self.path[0]
        dx, dy = next_x - self.x, next_y - self.y
        dist = math.hypot(dx, dy)
        if dist < self.speed * 2:
            self.path.pop(0)
            if self.path: dx, dy, dist = self.path[0][0] - self.x, self.path[0][1] - self.y, math.hypot(self.path[0][0] - self.x, self.path[0][1] - self.y)
        if dist > 0:
            s = self.speed * get_speed_mod(self.x, self.y)
            if not is_obstacle_fn(self.x + (dx/dist)*s, self.y): self.x += (dx/dist)*s
            if not is_obstacle_fn(self.x, self.y + (dy/dist)*s): self.y += (dy/dist)*s

    def update(self, res_dict, buildings_list, trees_list, crystals_list, enemies_list, is_obstacle_fn, get_speed_mod, effects_list, game_map, MAP_COLS, MAP_ROWS, all_units):
        if self.is_hidden:
            if self.state == 'GARRISON':
                if not self.building_ref or self.building_ref.hp <= 0:
                    self.is_hidden, self.building_ref, self.state = False, None, 'IDLE' # Wieża zniszczona, wyjdź
            else:
                if not self.building_ref or self.building_ref.is_built or self.building_ref.hp <= 0:
                    self.is_hidden, self.building_ref, self.state = False, None, 'IDLE'
            return

        if self.attack_timer > 0: self.attack_timer -= 1
        closest_base = self.get_closest_base(buildings_list)

        if self.carry_amount > 0 and closest_base:
            if (closest_base.x - self.x)**2 + (closest_base.y - self.y)**2 <= (closest_base.radius + self.radius + 30)**2:
                if self.carry_type == 'wood': res_dict['wood'] += self.carry_amount
                elif self.carry_type == 'crystal': res_dict['crystals'] += self.carry_amount
                last_type, self.carry_amount, self.carry_type = self.carry_type, 0, None
                if self.state == 'RETURN':
                    if self.target_obj and getattr(self.target_obj, 'amount', 0) > 0: self.command_harvest(self.target_obj, game_map, MAP_COLS, MAP_ROWS, buildings_list)
                    else: 
                        self.search_type, self.state = last_type, 'SEARCH_MOVE'
                        self.calculate_path(self.last_harvest_x, self.last_harvest_y, game_map, MAP_COLS, MAP_ROWS, buildings_list)

        if self.state == 'IDLE':
            target, min_d_sq = None, self.vision_range * self.vision_range
            for e in enemies_list:
                d_sq = (e.x - self.x)**2 + (e.y - self.y)**2
                if d_sq < min_d_sq: target, min_d_sq = e, d_sq
            if target: self.command_attack(target, game_map, MAP_COLS, MAP_ROWS, buildings_list)
            elif self.u_type == 'worker':
                # Poszukiwanie Złóż z Limitami [Baza Treningowa: Optymalizacja przydziału zadań agentom]
                best_res = get_available_resource(self, trees_list + crystals_list, all_units)
                if best_res and ((best_res.x - self.x)**2 + (best_res.y - self.y)**2) < (self.radius + 60)**2:
                    self.command_harvest(best_res, game_map, MAP_COLS, MAP_ROWS, buildings_list)

        elif self.state == 'MOVE':
            self._follow_path(buildings_list, is_obstacle_fn, get_speed_mod)
            if not self.path and (self.target_x - self.x)**2 + (self.target_y - self.y)**2 < self.speed*self.speed: self.state = 'IDLE'

        elif self.state == 'ATTACK':
            if not self.target_obj or getattr(self.target_obj, 'hp', 0) <= 0: self.state = 'IDLE'; return
            dist = math.hypot(self.target_obj.x - self.x, self.target_obj.y - self.y)
            if dist > self.attack_range + self.target_obj.radius:
                if not self.path and random.random() < 0.05: self.calculate_path(self.target_obj.x, self.target_obj.y, game_map, MAP_COLS, MAP_ROWS, buildings_list)
                self._follow_path(buildings_list, is_obstacle_fn, get_speed_mod)
            else:
                self.path = [] 
                if self.attack_timer <= 0:
                    self.target_obj.hp -= self.damage
                    self.attack_timer = self.attack_cooldown
                    if self.attack_range > 50: effects_list.append({'x1': self.x, 'y1': self.y, 'x2': self.target_obj.x, 'y2': self.target_obj.y, 'timer': 8, 'color': WHITE})
                    if hasattr(self.target_obj, 'amount'): self.target_obj.amount = max(0, self.target_obj.amount - self.damage)

        elif self.state == 'BUILD':
            if math.hypot(self.target_x - self.x, self.target_y - self.y) < self.speed + 35: 
                self.is_hidden = True
                new_b = Building(self.target_obj['col'], self.target_obj['row'], self.target_obj['type'])
                buildings_list.append(new_b); self.building_ref = new_b
            else: self._follow_path(buildings_list, is_obstacle_fn, get_speed_mod)

        elif self.state == 'GARRISON':
            if math.hypot(self.target_obj.x - self.x, self.target_obj.y - self.y) < self.speed + 35:
                if not getattr(self.target_obj, 'garrisoned_unit', None):
                    self.is_hidden = True
                    self.target_obj.garrisoned_unit = self
                    self.building_ref = self.target_obj
                else: self.state = 'IDLE' # Wieża zajęta
            else: self._follow_path(buildings_list, is_obstacle_fn, get_speed_mod)

        elif self.state == 'HARVEST':
            if not self.target_obj or self.target_obj.amount <= 0: self.state = 'IDLE'; return
            dist = math.hypot(self.target_obj.x - self.x, self.target_obj.y - self.y)
            if dist > self.target_obj.radius + self.radius + 15:
                self._follow_path(buildings_list, is_obstacle_fn, get_speed_mod)
            else:
                self.path = []
                self.last_harvest_x, self.last_harvest_y = self.target_obj.x, self.target_obj.y
                self.harvest_timer += 1
                if self.harvest_timer > 60:
                    wg = min(10, self.target_obj.amount)
                    self.target_obj.amount -= wg
                    self.target_obj.hp -= wg 
                    self.carry_amount, self.carry_type, self.harvest_timer, self.state = wg, self.target_obj.type, 0, 'RETURN'
                    if closest_base: self.calculate_path(closest_base.x, closest_base.y, game_map, MAP_COLS, MAP_ROWS, buildings_list)

        elif self.state == 'RETURN':
            if not closest_base: self.state = 'IDLE'; return
            self._follow_path(buildings_list, is_obstacle_fn, get_speed_mod)

        elif self.state == 'SEARCH_MOVE':
            if not self.path and (self.target_x - self.x)**2 + (self.target_y - self.y)**2 > self.speed*self.speed:
                self._follow_path(buildings_list, is_obstacle_fn, get_speed_mod)
            elif not self.path:
                best_res = get_available_resource(self, trees_list + crystals_list, all_units)
                if best_res: self.command_harvest(best_res, game_map, MAP_COLS, MAP_ROWS, buildings_list)
                else: self.state = 'IDLE'

    def draw(self, surface, cam_x, cam_y):
        if self.is_hidden: return 
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        col = YELLOW if self.carry_type == 'wood' else CYAN if self.carry_type == 'crystal' else self.color
        pygame.draw.circle(surface, col, (sx, sy), self.radius)
        if self.is_selected: pygame.draw.circle(surface, GREEN, (sx, sy), self.radius + 2, 2)
        draw_hp_bar(surface, sx, sy, self.hp, self.max_hp)

class Zombie:
    def __init__(self, x, y):
        self.x, self.y = x, y
        st = UNIT_STATS['zombie']
        self.speed, self.radius, self.is_selected = st['speed'], 14, False 
        self.title, self.vision_range, self.color = st['title'], st['vision'], (50, 120, 50)
        self.hp, self.max_hp = st['hp'], st['hp']
        self.damage, self.attack_range, self.attack_cooldown, self.attack_timer = st['damage'], st['range'], st['cooldown'], 0
        self.path = []

    def update(self, player_units, player_buildings, is_obstacle_fn, get_speed_mod, effects_list, game_map, MAP_COLS, MAP_ROWS):
        if self.attack_timer > 0: self.attack_timer -= 1
        
        target, min_dist = None, 999999
        valid_targets = [u for u in player_units if not u.is_hidden] + [b for b in player_buildings if b.b_type != 'cemetery']
        
        # Atak zależy od tego czy zombie widzi cel (True FoW odnosi się do nas, ale zombie niech skanują normalnie)
        for obj in valid_targets:
            d = math.hypot(obj.x - self.x, obj.y - self.y)
            if d < min_dist: target, min_dist = obj, d
            
        if target:
            if min_dist > self.attack_range + getattr(target, 'radius', 0):
                if not self.path and random.random() < 0.05: # Zombie rzadziej przeliczają ścieżki
                    self.path = get_astar_path((self.x//TILE_SIZE, self.y//TILE_SIZE), (target.x//TILE_SIZE, target.y//TILE_SIZE), game_map, MAP_COLS, MAP_ROWS, player_buildings, is_zombie=True)
                
                if self.path:
                    nx, ny = self.path[0]
                    dx, dy = nx - self.x, ny - self.y
                    dist = math.hypot(dx, dy)
                    if dist < self.speed * 2:
                        self.path.pop(0)
                        if self.path: dx, dy, dist = self.path[0][0] - self.x, self.path[0][1] - self.y, math.hypot(self.path[0][0] - self.x, self.path[0][1] - self.y)
                    if dist > 0:
                        s = self.speed * get_speed_mod(self.x, self.y)
                        if not is_obstacle_fn(self.x + (dx/dist)*s, self.y): self.x += (dx/dist)*s
                        if not is_obstacle_fn(self.x, self.y + (dy/dist)*s): self.y += (dy/dist)*s
                else:
                    # Tępe podążanie
                    dx, dy = target.x - self.x, target.y - self.y
                    if min_dist > 0:
                        s = self.speed * get_speed_mod(self.x, self.y)
                        if not is_obstacle_fn(self.x + (dx/min_dist)*s, self.y): self.x += (dx/min_dist)*s
                        if not is_obstacle_fn(self.x, self.y + (dy/min_dist)*s): self.y += (dy/min_dist)*s
            else:
                self.path = []
                if self.attack_timer <= 0:
                    target.hp -= self.damage
                    self.attack_timer = self.attack_cooldown

    def draw(self, surface, cam_x, cam_y):
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        pygame.draw.circle(surface, self.color, (sx, sy), self.radius)
        if self.is_selected: pygame.draw.circle(surface, RED, (sx, sy), self.radius + 2, 2)
        draw_hp_bar(surface, sx, sy, self.hp, self.max_hp)

def resolve_collisions(unit_list, buildings_list, is_obstacle_fn):
    for i in range(len(unit_list)):
        if getattr(unit_list[i], 'is_hidden', False): continue
        for j in range(i + 1, len(unit_list)):
            if getattr(unit_list[j], 'is_hidden', False): continue
            u1, u2 = unit_list[i], unit_list[j]
            dx, dy = u2.x - u1.x, u2.y - u1.y
            dist_sq = dx*dx + dy*dy
            min_dist = u1.radius + u2.radius
            if dist_sq < min_dist * min_dist:
                dist = math.sqrt(dist_sq)
                if dist == 0: dx, dy, dist = 1, 0, 1
                overlap = min_dist - dist
                px, py = (dx / dist) * (overlap * 0.15), (dy / dist) * (overlap * 0.15)
                
                u1_rect = pygame.Rect((u1.x - px) - u1.radius, (u1.y - py) - u1.radius, u1.radius*2, u1.radius*2)
                if not is_obstacle_fn(u1.x - px, u1.y - py) and not any(b.rect.colliderect(u1_rect) for b in buildings_list):
                    u1.x, u1.y = u1.x - px, u1.y - py
                u2_rect = pygame.Rect((u2.x + px) - u2.radius, (u2.y + py) - u2.radius, u2.radius*2, u2.radius*2)
                if not is_obstacle_fn(u2.x + px, u2.y + py) and not any(b.rect.colliderect(u2_rect) for b in buildings_list):
                    u2.x, u2.y = u2.x + px, u2.y + py

def is_visible(obj, cam_x, cam_y, w, h):
    obj_x = obj.x if hasattr(obj, 'x') else obj.rect.centerx
    obj_y = obj.y if hasattr(obj, 'y') else obj.rect.centery
    return (cam_x - 100 < obj_x < cam_x + w + 100) and (cam_y - 100 < obj_y < cam_y + h + 100)

def draw_resource_icon(surface, x, y, type_str):
    pygame.draw.circle(surface, GREEN if type_str == 'wood' else CYAN, (x, y), 6)