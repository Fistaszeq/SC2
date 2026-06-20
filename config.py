# config.py
import pygame

# --- WYMIARY I UKŁAD ---
WIDTH, HEIGHT = 1024, 768
UI_HEIGHT = 160
TOP_BAR_HEIGHT = 30
VIEW_HEIGHT = HEIGHT - TOP_BAR_HEIGHT - UI_HEIGHT 
TILE_SIZE = 50
MINIMAP_SIZE = 140

# --- PALETA KOLORÓW ---
WHITE, BLACK = (255, 255, 255), (0, 0, 0)
BLUE, GREEN, RED = (0, 120, 255), (0, 200, 0), (255, 50, 50)
DARK_GRAY, LIGHT_GRAY, YELLOW = (30, 30, 30), (120, 120, 120), (255, 200, 0)
CYAN, ORANGE, PURPLE = (0, 255, 255), (255, 165, 0), (150, 0, 255)
MAGENTA = (255, 0, 255)
UI_BORDER = (50, 60, 80)
NIGHT_COLOR = (5, 5, 20)

# --- KOLORY BIOMÓW ---
DIRT_COLOR = (101, 67, 33)
ROCK_COLOR = (128, 128, 128)
GRASS_COLOR = (39, 174, 96)   # Nowa ładna trawa
WATER_COLOR = (41, 128, 185)  # Rzeka

# --- SYSTEM CZASU ---
DAY_LENGTH_FRAMES = 14000

# =====================================================================
# MINI-PROGRAM BALANSUJĄCY (Zmień wartości tutaj, aby zmienić grę)
# =====================================================================
COSTS = {
    'house': (30, 10),
    'barracks': (50, 50),
    'wall': (10, 0),
    'tower': (40, 20),
    'base': (200, 100)
}

UNIT_STATS = {
    'worker': {
        'title': "Robotnik",
        'hp': 60,
        'damage': 6,
        'speed': 1.6,
        'range': 25,
        'cooldown': 80,
        'vision': 220,
        'cost_wood': 50,
        'cost_crystal': 0
    },
    'archer': {
        'title': "Łucznik",
        'hp': 85,
        'damage': 16,
        'speed': 2.1,
        'range': 220,
        'cooldown': 65,
        'vision': 280,
        'cost_wood': 40,
        'cost_crystal': 20
    },
    'zombie': {
        'title': "Zombie",
        'hp': 110,
        'damage': 12,
        'speed': 1.1,
        'range': 25,
        'cooldown': 85,
        'vision': 200
    }
}