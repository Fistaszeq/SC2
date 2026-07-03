import json

cols, rows = 40, 40
grid = [[0 for _ in range(cols)] for _ in range(rows)]

# Generowanie rzeki i bloku skalnego (Choke-point na środku mapy)
for r in range(rows):
    grid[r][20] = 5
    grid[r][21] = 5
    if r < 15 or r > 25:
        grid[r][19] = 1
        grid[r][22] = 1

# Generowanie strefy bazy gracza i piasku (Zachodnia flanka)
for r in range(30, 36):
    for c in range(4, 10):
        grid[r][c] = 6
grid[33][6] = 4

# Dystrybucja ułożonych strategicznie surowców
resources = [
    (28, 5, 2), (28, 6, 2), (28, 7, 2), (29, 6, 2), (27, 6, 2), # Drewno
    (35, 12, 3), (36, 12, 3), (35, 13, 3),                      # Kryształy
    (31, 2, 8), (32, 2, 8), (32, 3, 8), (33, 2, 8)              # Kamień
]
for r, c, val in resources:
    grid[r][c] = val

# Dodatkowe pojedyncze lasy na zewnątrz bazy
for r, c in [(10, 10), (11, 10), (10, 11), (30, 25), (31, 26), (30, 26)]:
    grid[r][c] = 2

# Generowanie cmentarzy (Wschodnia flanka)
grid[5][35] = 7
grid[35][35] = 7

# Definicja pliku JSON
map_data = {
    "name": "poziom_1",
    "cols": cols,
    "rows": rows,
    "horde_day": 3,
    "horde_size": 40,
    "wave_interval_hours": 12,
    "wave_size": 8,
    "grid": grid
}

with open("poziom_1.json", "w") as f:
    json.dump(map_data, f)
    
print("Pomyślnie wygenerowano plik: poziom_1.json")