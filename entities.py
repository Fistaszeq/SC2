# entities.py
import math
import random
import pygame
from config import *

def draw_hp_bar(surface, x, y, hp, max_hp, width=30):
    if hp < max_hp or hp <= 0:
        bar_w, bar_h = width, 4
        bx, by = x - bar_w // 2, y - 20
        pygame.draw.rect(surface, RED, (bx, by, bar_w, bar_h))
        pygame.draw.rect(surface, GREEN, (bx, by, int(bar_w * (max(0, hp) / max_hp)), bar_h))

class Tree:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.radius = random.randint(12, 28)
        self.amount = self.max_amount = self.radius * 20 
        self.hp = self.max_hp = self.amount
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
        self.is_selected, self.type, self.title = False, 'crystal', "Złoże Kryształów"
        self.color = CYAN
    def draw_hp(self, surface, cam_x, cam_y):
        if self.hp < self.max_hp: draw_hp_bar(surface, int(self.x - cam_x), int(self.y - cam_y), self.hp, self.max_hp)

class Building:
    def __init__(self, x, y, b_type, rotation=0):
        self.x, self.y, self.b_type, self.rotation = x, y, b_type, rotation
        self.is_selected, self.is_built, self.build_progress = False, False, 0
        self.hp, self.max_hp = 1, 100
        self.vision_range = 150
        self.recruit_queue, self.recruit_progress, self.recruit_time_max = 0, 0, 180
        self.attack_timer = 0
        self.rally_x, self.rally_y = x + 80, y + 80
        
        if b_type == 'house':
            self.title, self.radius, self.color, self.max_hp, self.build_max = "Domek", 25, ORANGE, 200, 500
            self.rect = pygame.Rect(x - 25, y - 25, 50, 50)
        elif b_type == 'barracks':
            self.title, self.radius, self.color, self.max_hp, self.build_max = "Baraki", 35, PURPLE, 400, 600
            self.rect = pygame.Rect(x - 35, y - 35, 70, 70)
            self.recruit_time_max = 240 
        elif b_type == 'tower':
            self.title, self.radius, self.color, self.max_hp, self.build_max = "Wieżyczka", 20, LIGHT_GRAY, 300, 300
            self.rect = pygame.Rect(x - 20, y - 20, 40, 40)
            self.vision_range = 300
            self.damage = 15
        elif b_type == 'base':
            self.title, self.radius, self.color, self.max_hp, self.build_max = "Baza", 45, RED, 1500, 800
            self.rect = pygame.Rect(x - 45, y - 45, 90, 90)
            self.vision_range = 400
        elif b_type == 'wall':
            self.title, self.radius, self.color, self.max_hp, self.build_max = "Mur", 15, LIGHT_GRAY, 500, 150
            w, h = (60, 20) if rotation == 0 else (20, 60)
            self.rect = pygame.Rect(x - w//2, y - h//2, w, h)
        elif b_type == 'cemetery':
            self.title, self.radius, self.color, self.max_hp, self.build_max = "Cmentarz", 35, (50, 20, 50), 800, 100
            self.rect = pygame.Rect(x - 35, y - 35, 70, 70)
            self.is_built = True
            self.hp = self.max_hp
            self.spawn_timer = 0

    def update(self, enemies_list, effects_list, is_night=False):
        if not self.is_built:
            self.build_progress += 1
            self.hp = max(1, int(self.max_hp * (self.build_progress / self.build_max)))
            if self.build_progress >= self.build_max: self.is_built = True
        else:
            if self.b_type in ['base', 'barracks']:
                if self.recruit_queue > 0:
                    self.recruit_progress += 1
                    if self.recruit_progress >= self.recruit_time_max:
                        self.recruit_progress, self.recruit_queue = 0, self.recruit_queue - 1
                        return 'spawn_worker' if self.b_type == 'base' else 'spawn_archer'
                else: self.recruit_progress = 0
            
            if self.b_type == 'tower':
                if self.attack_timer > 0: self.attack_timer -= 1
                elif enemies_list:
                    for e in enemies_list:
                        dx, dy = e.x - self.x, e.y - self.y
                        if (dx*dx + dy*dy) <= (self.vision_range * self.vision_range):
                            e.hp -= self.damage
                            effects_list.append({'x1': self.x, 'y1': self.y, 'x2': e.x, 'y2': e.y, 'timer': 8, 'color': YELLOW})
                            self.attack_timer = 60 
                            break
                            
            if self.b_type == 'cemetery':
                self.spawn_timer += 1
                threshold = 240 if is_night else 1200 
                if self.spawn_timer >= threshold:
                    self.spawn_timer = 0
                    return 'spawn_zombie'
        return None

    def draw(self, surface, cam_x, cam_y):
        hx, hy = int(self.x - cam_x), int(self.y - cam_y)
        if self.b_type == 'wall':
            draw_rect = self.rect.move(-cam_x, -cam_y)
            pygame.draw.rect(surface, self.color if self.is_built else (150, 100, 0), draw_rect, 0 if self.is_built else 2)
            if self.is_selected: pygame.draw.rect(surface, WHITE, draw_rect, 2)
        else:
            if not self.is_built:
                pygame.draw.circle(surface, (150, 100, 0), (hx, hy), self.radius, 2)
                pygame.draw.rect(surface, GREEN, (hx - 20, hy - 35, int(40 * (self.build_progress / self.build_max)), 6))
            else:
                if self.b_type == 'cemetery':
                    pygame.draw.circle(surface, (20, 20, 20), (hx, hy), self.radius)
                    pygame.draw.rect(surface, (80, 80, 80), (hx-10, hy-20, 20, 40)) 
                else:
                    pygame.draw.circle(surface, self.color, (hx, hy), self.radius)
                
                if self.b_type == 'tower' and self.is_selected:
                    s = pygame.Surface((self.vision_range*2, self.vision_range*2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (255, 0, 0, 50), (self.vision_range, self.vision_range), self.vision_range)
                    surface.blit(s, (hx - self.vision_range, hy - self.vision_range))
            if self.is_selected: pygame.draw.circle(surface, WHITE, (hx, hy), self.radius + 2, 1)
            
            if self.b_type in ['base', 'barracks'] and self.is_built and self.is_selected:
                rx, ry = int(self.rally_x - cam_x), int(self.rally_y - cam_y)
                pygame.draw.line(surface, WHITE, (hx, hy), (rx, ry), 1)
                pygame.draw.circle(surface, GREEN, (rx, ry), 5)
                if self.recruit_queue > 0:
                    pygame.draw.rect(surface, DARK_GRAY, (hx - 30, hy - self.radius - 25, 60, 8))
                    pygame.draw.rect(surface, GREEN, (hx - 30, hy - self.radius - 25, int(60 * (self.recruit_progress / self.recruit_time_max)), 8))
            
        draw_hp_bar(surface, hx, hy, self.hp, self.max_hp)

class Unit:
    def __init__(self, x, y, u_type='worker'):
        self.x, self.y, self.u_type = x, y, u_type
        self.is_selected, self.state = False, 'IDLE'
        self.target_obj, self.target_x, self.target_y = None, x, y
        self.carry_type, self.carry_amount, self.harvest_timer = None, 0, 0
        self.last_harvest_x, self.last_harvest_y, self.search_type = x, y, None
        
        st = UNIT_STATS[u_type]
        self.title, self.speed, self.radius = st['title'], st['speed'], (12 if u_type == 'worker' else 10)
        self.hp = self.max_hp = st['hp']
        self.vision_range, self.damage = st['vision'], st['damage']
        self.attack_range, self.attack_cooldown = st['range'], st['cooldown']
        self.color = BLUE if u_type == 'worker' else (150, 200, 150)
        self.attack_timer = 0

    def command_move(self, tx, ty): self.state, self.target_x, self.target_y, self.target_obj = 'MOVE', tx, ty, None
    def command_harvest(self, resource_obj): self.state, self.target_obj = 'HARVEST', resource_obj
    def command_attack(self, obj): self.state, self.target_obj = 'ATTACK', obj
    def command_build(self, tx, ty, b_type, rot): self.state, self.target_x, self.target_y, self.target_obj = 'BUILD', tx, ty, {'type': b_type, 'rot': rot}
    def command_stop(self): self.state, self.target_obj, self.target_x, self.target_y = 'IDLE', None, self.x, self.y

    def get_closest_base(self, buildings_list):
        bases = [b for b in buildings_list if b.b_type == 'base' and b.is_built and b.hp > 0]
        if not bases: return None
        return min(bases, key=lambda b: (b.x - self.x)**2 + (b.y - self.y)**2)

    def update(self, res_dict, buildings_list, trees_list, crystals_list, enemies_list, is_obstacle_fn, get_speed_mod, effects_list):
        if self.attack_timer > 0: self.attack_timer -= 1
        closest_base = self.get_closest_base(buildings_list)

        if self.carry_amount > 0 and closest_base:
            dx, dy = closest_base.x - self.x, closest_base.y - self.y
            if (dx*dx + dy*dy) <= (closest_base.radius + self.radius + 30)**2:
                if self.carry_type == 'wood': res_dict['wood'] += self.carry_amount
                elif self.carry_type == 'crystal': res_dict['crystals'] += self.carry_amount
                last_type = self.carry_type
                self.carry_amount, self.carry_type = 0, None
                if self.state == 'RETURN':
                    if self.target_obj and getattr(self.target_obj, 'amount', 0) > 0: self.state = 'HARVEST'
                    else: self.target_x, self.target_y, self.search_type, self.state = self.last_harvest_x, self.last_harvest_y, last_type, 'SEARCH_MOVE'

        if self.state == 'IDLE':
            target, min_d_sq = None, self.vision_range * self.vision_range
            for e in enemies_list:
                d_sq = (e.x - self.x)**2 + (e.y - self.y)**2
                if d_sq < min_d_sq: target, min_d_sq = e, d_sq
                
            if target:
                self.command_attack(target)
            elif self.u_type == 'worker':
                nearest_res, min_dist_sq = None, (self.radius + 40)**2
                for t in trees_list:
                    d_sq = (t.x - self.x)**2 + (t.y - self.y)**2
                    if d_sq < min_dist_sq: nearest_res, min_dist_sq = t, d_sq
                for c in crystals_list:
                    d_sq = (c.x - self.x)**2 + (c.y - self.y)**2
                    if d_sq < min_dist_sq: nearest_res, min_dist_sq = c, d_sq
                if nearest_res: self.command_harvest(nearest_res)

        elif self.state == 'MOVE':
            self._move_towards(self.target_x, self.target_y, buildings_list, is_obstacle_fn, get_speed_mod)
            if (self.target_x - self.x)**2 + (self.target_y - self.y)**2 < self.speed*self.speed: self.state = 'IDLE'

        elif self.state == 'ATTACK':
            if not self.target_obj or getattr(self.target_obj, 'hp', 0) <= 0: 
                self.state = 'IDLE'; return
            dist = math.hypot(self.target_obj.x - self.x, self.target_obj.y - self.y)
            if dist > self.attack_range + self.target_obj.radius:
                self._move_towards(self.target_obj.x, self.target_obj.y, buildings_list, is_obstacle_fn, get_speed_mod)
            else:
                if self.attack_timer <= 0:
                    self.target_obj.hp -= self.damage
                    self.attack_timer = self.attack_cooldown
                    if self.attack_range > 50:
                        effects_list.append({'x1': self.x, 'y1': self.y, 'x2': self.target_obj.x, 'y2': self.target_obj.y, 'timer': 8, 'color': WHITE})
                    if hasattr(self.target_obj, 'amount'): self.target_obj.amount = max(0, self.target_obj.amount - self.damage)

        elif self.state == 'BUILD':
            self._move_towards(self.target_x, self.target_y, buildings_list, is_obstacle_fn, get_speed_mod)
            if (self.target_x - self.x)**2 + (self.target_y - self.y)**2 < (self.speed + 15)**2: 
                buildings_list.append(Building(self.target_x, self.target_y, self.target_obj['type'], self.target_obj['rot']))
                angle = math.atan2(self.y - self.target_y, self.x - self.target_x)
                self.x, self.y = self.target_x + math.cos(angle) * 60, self.target_y + math.sin(angle) * 60
                self.state = 'IDLE' 

        elif self.state == 'HARVEST':
            if not self.target_obj or self.target_obj.amount <= 0: 
                self.state = 'IDLE'; return
            dist = math.hypot(self.target_obj.x - self.x, self.target_obj.y - self.y)
            if dist > self.target_obj.radius + self.radius + 15:
                self._move_towards(self.target_obj.x, self.target_obj.y, buildings_list, is_obstacle_fn, get_speed_mod)
            else:
                self.last_harvest_x, self.last_harvest_y = self.target_obj.x, self.target_obj.y
                self.harvest_timer += 1
                if self.harvest_timer > 60:
                    wg = min(10, self.target_obj.amount)
                    self.target_obj.amount -= wg
                    self.target_obj.hp -= wg 
                    self.carry_amount, self.carry_type, self.harvest_timer, self.state = wg, self.target_obj.type, 0, 'RETURN'

        elif self.state == 'RETURN':
            if not closest_base: self.state = 'IDLE'; return
            self._move_towards(closest_base.x, closest_base.y, buildings_list, is_obstacle_fn, get_speed_mod)

        elif self.state == 'SEARCH_MOVE':
            if (self.target_x - self.x)**2 + (self.target_y - self.y)**2 > self.speed*self.speed:
                self._move_towards(self.target_x, self.target_y, buildings_list, is_obstacle_fn, get_speed_mod)
            else:
                nearest_res, min_dist_sq = None, 750 * 750
                search_list = trees_list if self.search_type == 'wood' else crystals_list
                for obj in search_list:
                    d_sq = (obj.x - self.x)**2 + (obj.y - self.y)**2
                    if d_sq < min_dist_sq: nearest_res, min_dist_sq = obj, d_sq
                if nearest_res: self.command_harvest(nearest_res)
                else: self.state = 'IDLE'

    def _move_towards(self, tx, ty, buildings_list, is_obstacle_fn, get_speed_mod):
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            # Woda (rzeka) modyfikuje prędkość
            current_speed = self.speed * get_speed_mod(self.x, self.y)
            sx, sy = (dx / dist) * current_speed, (dy / dist) * current_speed
            
            can_move_x, can_move_y = True, True
            if is_obstacle_fn(self.x + sx, self.y): can_move_x = False
            if is_obstacle_fn(self.x, self.y + sy): can_move_y = False
            
            unit_rect_x = pygame.Rect(self.x + sx - self.radius, self.y - self.radius, self.radius*2, self.radius*2)
            unit_rect_y = pygame.Rect(self.x - self.radius, self.y + sy - self.radius, self.radius*2, self.radius*2)
            for b in buildings_list:
                if b.rect.colliderect(unit_rect_x): can_move_x = False
                if b.rect.colliderect(unit_rect_y): can_move_y = False

            if can_move_x: self.x += sx
            if can_move_y: self.y += sy

    def draw(self, surface, cam_x, cam_y):
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        col = self.color
        if self.u_type == 'worker': col = YELLOW if self.carry_type == 'wood' else CYAN if self.carry_type == 'crystal' else BLUE
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

    def update(self, player_units, player_buildings, is_obstacle_fn, get_speed_mod, effects_list):
        if self.attack_timer > 0: self.attack_timer -= 1
        
        target, min_dist = None, 999999
        valid_targets = player_units + [b for b in player_buildings if b.b_type != 'cemetery']
        
        for obj in valid_targets:
            d = math.hypot(obj.x - self.x, obj.y - self.y)
            if d < min_dist: target, min_dist = obj, d
            
        if target:
            if min_dist > self.attack_range + target.radius:
                dx, dy = target.x - self.x, target.y - self.y
                if min_dist > 0:
                    current_speed = self.speed * get_speed_mod(self.x, self.y)
                    sx, sy = (dx / min_dist) * current_speed, (dy / min_dist) * current_speed
                    if not is_obstacle_fn(self.x + sx, self.y): self.x += sx
                    if not is_obstacle_fn(self.x, self.y + sy): self.y += sy
            else:
                if self.attack_timer <= 0:
                    target.hp -= self.damage
                    self.attack_timer = self.attack_cooldown

    def draw(self, surface, cam_x, cam_y):
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        pygame.draw.circle(surface, self.color, (sx, sy), self.radius)
        if self.is_selected: pygame.draw.circle(surface, RED, (sx, sy), self.radius + 2, 2)
        draw_hp_bar(surface, sx, sy, self.hp, self.max_hp)

def resolve_collisions(unit_list, buildings_list, is_obstacle_fn):
    """Zoptymalizowana i wygładzona relaksacja kolizji (Jitter-Fix)"""
    for i in range(len(unit_list)):
        for j in range(i + 1, len(unit_list)):
            u1, u2 = unit_list[i], unit_list[j]
            dx, dy = u2.x - u1.x, u2.y - u1.y
            dist_sq = dx*dx + dy*dy
            min_dist = u1.radius + u2.radius
            if dist_sq < min_dist * min_dist:
                dist = math.sqrt(dist_sq)
                if dist == 0: dx, dy, dist = 1, 0, 1
                overlap = min_dist - dist
                
                # Zastosowanie amortyzacji w tłoku
                relax = 0.15 
                px, py = (dx / dist) * (overlap * relax), (dy / dist) * (overlap * relax)
                
                u1_rect = pygame.Rect((u1.x - px) - u1.radius, (u1.y - py) - u1.radius, u1.radius*2, u1.radius*2)
                if not is_obstacle_fn(u1.x - px, u1.y - py) and not any(b.rect.colliderect(u1_rect) for b in buildings_list):
                    u1.x, u1.y = u1.x - px, u1.y - py
                
                u2_rect = pygame.Rect((u2.x + px) - u2.radius, (u2.y + py) - u2.radius, u2.radius*2, u2.radius*2)
                if not is_obstacle_fn(u2.x + px, u2.y + py) and not any(b.rect.colliderect(u2_rect) for b in buildings_list):
                    u2.x, u2.y = u2.x + px, u2.y + py
                    
def is_visible(obj, cam_x, cam_y, w, h):
    """Odrzuca obiekty poza ekranem, oszczędzając zasoby procesora."""
    return (cam_x - 100 < obj.x < cam_x + w + 100) and (cam_y - 100 < obj.y < cam_y + h + 100)

def draw_resource_icon(surface, x, y, type_str):
    """Rysuje małą ikonkę surowca na interfejsie użytkownika."""
    # (0, 200, 0) to GREEN, (0, 255, 255) to CYAN
    pygame.draw.circle(surface, (0, 200, 0) if type_str == 'wood' else (0, 255, 255), (x, y), 6)