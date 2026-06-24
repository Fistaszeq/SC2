# pathfinding.py
import heapq

def heuristic(a, b):
    # Heurystyka Manhattan dla siatek kwadratowych [Źródło: Algorytmy A* w przestrzeniach 2D]
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def get_astar_path(start_pos, target_pos, game_map, MAP_COLS, MAP_ROWS, buildings):
    """
    Zwraca ścieżkę w postaci listy współrzędnych pikseli (środków kafelków).
    Wymaga start_pos i target_pos w formacie (col, row).
    """
    start = (int(start_pos[0]), int(start_pos[1]))
    goal = (int(target_pos[0]), int(target_pos[1]))
    
    if start == goal:
        return []

    # Dynamiczna siatka przeszkód uwzględniająca budynki [Baza Treningowa: Operacje Macierzowe]
    blocked_grid = [[False for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]
    for r in range(MAP_ROWS):
        for c in range(MAP_COLS):
            if game_map[r][c] == 1: blocked_grid[r][c] = True # Skały
    
    # Dodanie budynków do siatki blokad
    for b in buildings:
        for br in range(b.row, b.row + b.h_tiles):
            for bc in range(b.col, b.col + b.w_tiles):
                if 0 <= br < MAP_ROWS and 0 <= bc < MAP_COLS:
                    blocked_grid[br][bc] = True

    # Jeśli cel jest zablokowany (np. kliknięto w budynek/surowiec), szukamy najbliższego wolnego sąsiada
    if blocked_grid[goal[1]][goal[0]]:
        found_adjacent = False
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
            nr, nc = goal[1] + dr, goal[0] + dc
            if 0 <= nr < MAP_ROWS and 0 <= nc < MAP_COLS and not blocked_grid[nr][nc]:
                goal = (nc, nr)
                found_adjacent = True
                break
        if not found_adjacent:
            return [] # Brak możliwości dojścia

    frontier = []
    heapq.heappush(frontier, (0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}

    while frontier:
        current = heapq.heappop(frontier)[1]

        if current == goal:
            break

        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
            next_node = (current[0] + dx, current[1] + dy)
            nx, ny = next_node
            
            if 0 <= nx < MAP_COLS and 0 <= ny < MAP_ROWS and not blocked_grid[ny][nx]:
                # Woda (5) kosztuje podwójnie
                terrain_cost = 2.0 if game_map[ny][nx] == 5 else 1.0
                # Ruch na ukos jest nieznacznie droższy
                move_cost = 1.41 if dx != 0 and dy != 0 else 1.0 
                new_cost = cost_so_far[current] + (terrain_cost * move_cost)
                
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + heuristic(goal, next_node)
                    heapq.heappush(frontier, (priority, next_node))
                    came_from[next_node] = current

    if goal not in came_from:
        return []

    # Odtwarzanie ścieżki
    path = []
    current = goal
    while current != start:
        path.append(current)
        current = came_from[current]
    path.reverse()

    # Konwersja współrzędnych siatki (col, row) na współrzędne w pikselach świata (x, y) - środek kafla
    TILE_SIZE = 50
    pixel_path = [((c * TILE_SIZE) + TILE_SIZE//2, (r * TILE_SIZE) + TILE_SIZE//2) for c, r in path]
    return pixel_path