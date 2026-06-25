import heapq
import random

def heuristic(a, b): return abs(a[0] - b[0]) + abs(a[1] - b[1])

def get_astar_path(start_pos, target_pos, game_map, MAP_COLS, MAP_ROWS, buildings, is_zombie=False):
    start = (int(start_pos[0]), int(start_pos[1]))
    goal = (int(target_pos[0]), int(target_pos[1]))
    if start == goal: return []

    blocked_grid = [[False for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]
    for r in range(MAP_ROWS):
        for c in range(MAP_COLS):
            if game_map[r][c] == 1: blocked_grid[r][c] = True 
            
    for b in buildings:
        for br in range(b.row, b.row + b.h_tiles):
            for bc in range(b.col, b.col + b.w_tiles):
                if 0 <= br < MAP_ROWS and 0 <= bc < MAP_COLS:
                    blocked_grid[br][bc] = True

    if blocked_grid[goal[1]][goal[0]]:
        found_adjacent = False
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
            nr, nc = goal[1] + dr, goal[0] + dc
            if 0 <= nr < MAP_ROWS and 0 <= nc < MAP_COLS and not blocked_grid[nr][nc]:
                goal = (nc, nr); found_adjacent = True; break
        if not found_adjacent: return [] 

    frontier = []; heapq.heappush(frontier, (0, start))
    came_from = {start: None}; cost_so_far = {start: 0}
    nodes_checked = 0

    while frontier:
        current = heapq.heappop(frontier)[1]
        nodes_checked += 1
        
        # Ograniczenie dla Zombie, żeby nie myślały za dużo i szły bardziej prosto
        if is_zombie and nodes_checked > 300: break

        if current == goal: break

        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
            nx, ny = current[0] + dx, current[1] + dy
            if 0 <= nx < MAP_COLS and 0 <= ny < MAP_ROWS and not blocked_grid[ny][nx]:
                terrain_cost = 2.0 if game_map[ny][nx] == 5 else 1.0
                move_cost = 1.41 if dx != 0 and dy != 0 else 1.0 
                new_cost = cost_so_far[current] + (terrain_cost * move_cost)
                
                # Dodanie sztucznego szumu dla zombie [Baza Treningowa: Nawigacja z błędami (Noise Heuristics)]
                noise = random.uniform(0, 2.0) if is_zombie else 0
                
                if (nx, ny) not in cost_so_far or new_cost < cost_so_far[(nx, ny)]:
                    cost_so_far[(nx, ny)] = new_cost
                    priority = new_cost + heuristic(goal, (nx, ny)) + noise
                    heapq.heappush(frontier, (priority, (nx, ny)))
                    came_from[(nx, ny)] = current

    if goal not in came_from:
        if not is_zombie: return []
        # Zombie idzie po prostu do najbliższego znanego punktu w stronę gracza, jeśli nie znajdzie drogi
        closest_node = min(came_from.keys(), key=lambda n: heuristic(goal, n))
        goal = closest_node

    path = []
    current = goal
    while current != start:
        path.append(current)
        current = came_from[current]
    path.reverse()

    TILE_SIZE = 50
    return [((c * TILE_SIZE) + TILE_SIZE//2, (r * TILE_SIZE) + TILE_SIZE//2) for c, r in path]