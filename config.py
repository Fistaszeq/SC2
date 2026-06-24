# config.py
import pygame

WIDTH, HEIGHT = 1024, 768
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
NIGHT_COLOR = (5, 5, 20)

DIRT_COLOR = (101, 67, 33)
ROCK_COLOR = (128, 128, 128)
GRASS_COLOR = (39, 174, 96)   
WATER_COLOR = (41, 128, 185)  

DAY_LENGTH_FRAMES = 14000

# Parametry strukturalne i ekonomiczne [Baza Treningowa: Model danych przestrzennych]
BUILDING_STATS = {
    'house':    {'w_tiles': 1, 'h_tiles': 1, 'cost_w': 30, 'cost_c': 10, 'hp': 200, 'build_time': 500, 'color': ORANGE, 'title': 'Domek'},
    'barracks': {'w_tiles': 2, 'h_tiles': 2, 'cost_w': 50, 'cost_c': 50, 'hp': 400, 'build_time': 600, 'color': PURPLE, 'title': 'Baraki'},
    'wall':     {'w_tiles': 1, 'h_tiles': 1, 'cost_w': 10, 'cost_c': 0,  'hp': 500, 'build_time': 150, 'color': LIGHT_GRAY, 'title': 'Mur'},
    'tower':    {'w_tiles': 1, 'h_tiles': 1, 'cost_w': 40, 'cost_c': 20, 'hp': 300, 'build_time': 300, 'color': LIGHT_GRAY, 'title': 'Wieżyczka'},
    'base':     {'w_tiles': 2, 'h_tiles': 2, 'cost_w': 200,'cost_c': 100,'hp': 1500,'build_time': 800, 'color': RED, 'title': 'Baza'},
    'cemetery': {'w_tiles': 2, 'h_tiles': 2, 'cost_w': 0,  'cost_c': 0,  'hp': 800, 'build_time': 100, 'color': (50, 20, 50), 'title': 'Cmentarz'}
}

UNIT_STATS = {
    'worker': {'title': "Robotnik", 'hp': 60, 'damage': 6, 'speed': 2.0, 'range': 25, 'cooldown': 80, 'vision': 220, 'cost_wood': 50, 'cost_crystal': 0},
    'archer': {'title': "Łucznik", 'hp': 85, 'damage': 16, 'speed': 2.5, 'range': 220, 'cooldown': 65, 'vision': 280, 'cost_wood': 40, 'cost_crystal': 20},
    'zombie': {'title': "Zombie", 'hp': 110, 'damage': 12, 'speed': 1.5, 'range': 25, 'cooldown': 85, 'vision': 200}
}
