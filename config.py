import pygame

WIDTH = 1024
HEIGHT = 768
UI_HEIGHT = 160
TOP_BAR_HEIGHT = 30
VIEW_HEIGHT = HEIGHT - TOP_BAR_HEIGHT - UI_HEIGHT 
TILE_SIZE = 50
MINIMAP_SIZE = 140

WHITE, BLACK = (255, 255, 255), (0, 0, 0)
BLUE, GREEN, RED = (0, 120, 255), (0, 200, 0), (255, 50, 50)
DARK_GRAY, LIGHT_GRAY, YELLOW = (30, 30, 30), (120, 120, 120), (255, 200, 0)
CYAN, ORANGE, PURPLE = (0, 255, 255), (255, 165, 0), (150, 0, 255)
MAGENTA = (255, 0, 255)
UI_BORDER = (50, 60, 80)

DIRT_COLOR = (101, 67, 33)
ROCK_COLOR = (128, 128, 128)
GRASS_COLOR = (39, 174, 96)   
WATER_COLOR = (41, 128, 185)  

DAY_LENGTH_FRAMES = 14000

# Słownik do podmieniania obiektów na własne grafiki (ścieżki do obrazów).
# Załączono dedykowane kafelki wygładzające piasek.
IMAGE_PATHS = {
    'worker': '',
    'archer': '',
    'zombie': '',
    'house': '',
    'wood_wall': '',
    'stone_wall': '',
    'torch': '',
    'large_torch': '',
    'tower': '',
    'double_tower': '',
    'obs_tower': '',
    'artillery': '',
    'base': '',
    'workshop': '',
    'barracks': '',
    'cemetery': '',
    'wood': '',
    'crystal': '',
    'stone': 'medium_stone-1.png.png',
    
    # Tereny
    'bg_grass': 'img/grass64.png',
    'bg_dirt': 'img/sand64.png',
    'bg_dirt_t':  'img/grass64.png',
    'bg_dirt_b':  'img/grass64.png',
    'bg_dirt_l':  'img/grass64.png',
    'bg_dirt_r':  'img/grass64.png',
    'bg_dirt_tl': 'img/grass64.png',
    'bg_dirt_tr': 'img/grass64.png',
    'bg_dirt_bl': 'img/grass64.png',
    'bg_dirt_br': 'img/grass64.png',
    'bg_water': '',
    'bg_rock': ''
}

UNIT_STATS = {
    'worker': {'speed': 1.8, 'hp': 50, 'vision': 150, 'damage': 5, 'range': 15, 'cooldown': 40, 'cost_wood': 50, 'cost_crystal': 0, 'cost_stone': 0, 'title': 'Robotnik'},
    'archer': {'speed': 2.1, 'hp': 80, 'vision': 250, 'damage': 15, 'range': 180, 'cooldown': 60, 'cost_wood': 60, 'cost_crystal': 20, 'cost_stone': 0, 'title': 'Łucznik'},
    'zombie': {'speed': 1.2, 'hp': 100, 'vision': 200, 'damage': 10, 'range': 15, 'cooldown': 45, 'title': 'Zombie'}
}

BUILDING_STATS = {
    'house':       {'w_tiles': 1, 'h_tiles': 1, 'cost_w': 30, 'cost_c': 0,  'cost_s': 0,  'hp': 200, 'build_time': 200, 'color': BLUE, 'title': 'Magazyn / Dom'},
    'wood_wall':   {'w_tiles': 1, 'h_tiles': 1, 'cost_w': 10, 'cost_c': 0,  'cost_s': 0,  'hp': 200, 'build_time': 100, 'color': (139, 69, 19), 'title': 'Drev. Mur'},
    'stone_wall':  {'w_tiles': 1, 'h_tiles': 1, 'cost_w': 0,  'cost_c': 0,  'cost_s': 15, 'hp': 500, 'build_time': 200, 'color': (100, 100, 100), 'title': 'Kam. Mur'},
    'torch':       {'w_tiles': 1, 'h_tiles': 1, 'cost_w': 10, 'cost_c': 0,  'cost_s': 0,  'hp': 50,  'build_time': 50,  'color': (200, 100, 0), 'title': 'Pochodnia'},
    'large_torch': {'w_tiles': 1, 'h_tiles': 1, 'cost_w': 25, 'cost_c': 0,  'cost_s': 10, 'hp': 150, 'build_time': 120, 'color': (255, 120, 0), 'title': 'Duża Poch.'},
    'tower':       {'w_tiles': 1, 'h_tiles': 1, 'cost_w': 40, 'cost_c': 20, 'cost_s': 10, 'hp': 300, 'build_time': 300, 'color': LIGHT_GRAY, 'title': 'Wieżyczka'},
    'double_tower':{'w_tiles': 1, 'h_tiles': 1, 'cost_w': 80, 'cost_c': 40, 'cost_s': 20, 'hp': 400, 'build_time': 400, 'color': LIGHT_GRAY, 'title': 'Podwójne Dzi.'},
    'obs_tower':   {'w_tiles': 1, 'h_tiles': 1, 'cost_w': 25, 'cost_c': 5,  'cost_s': 0,  'hp': 250, 'build_time': 250, 'color': (200, 200, 150), 'title': 'Wieża Obs.'},
    'artillery':   {'w_tiles': 2, 'h_tiles': 2, 'cost_w': 150,'cost_c': 80, 'cost_s': 50, 'hp': 500, 'build_time': 600, 'color': (150, 80, 50), 'title': 'Artyleria'},
    'base':        {'w_tiles': 2, 'h_tiles': 2, 'cost_w': 200,'cost_c': 100,'cost_s': 0,  'hp': 1500,'build_time': 800, 'color': RED, 'title': 'Baza'},
    'workshop':    {'w_tiles': 2, 'h_tiles': 2, 'cost_w': 80, 'cost_c': 40, 'cost_s': 20, 'hp': 600, 'build_time': 450, 'color': (100, 100, 150), 'title': 'Warsztat'},
    'barracks':    {'w_tiles': 2, 'h_tiles': 2, 'cost_w': 50, 'cost_c': 50, 'cost_s': 0,  'hp': 400, 'build_time': 600, 'color': PURPLE, 'title': 'Baraki'},
    'cemetery':    {'w_tiles': 2, 'h_tiles': 2, 'cost_w': 0,  'cost_c': 0,  'cost_s': 0,  'hp': 1000,'build_time': 1, 'color': (50, 20, 50), 'title': 'Cmentarz'}
}