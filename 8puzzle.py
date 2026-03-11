import heapq

def heuristic(state):
    goal = ((1, 2, 3), (4, 5, 6), (7, 8, 0))
    h = 0
    for i in range(3):
        for j in range(3):
            if state[i][j] == 0:
                continue
            goal_i = (state[i][j] - 1) // 3
            goal_j = (state[i][j] - 1) % 3
            h += abs(i - goal_i) + abs(j - goal_j)
    return h

def get_next_states(state):
    moves = []
    blank_i, blank_j = -1, -1
    for i in range(3):
        for j in range(3):
            if state[i][j] == 0:
                blank_i, blank_j = i, j
                break
        if blank_i != -1:
            break
    directions = [(-1, 0, 'Up'), (1, 0, 'Down'), (0, -1, 'Left'), (0, 1, 'Right')]
    for di, dj, move in directions:
        ni, nj = blank_i + di, blank_j + dj
        if 0 <= ni < 3 and 0 <= nj < 3:
            new_state = [list(row) for row in state]
            new_state[blank_i][blank_j] = new_state[ni][nj]
            new_state[ni][nj] = 0
            new_state_tuple = tuple(tuple(row) for row in new_state)
            moves.append((move, new_state_tuple))
    return moves

def is_solvable(puzzle: list) -> bool:
    # Calculate inversion count
    inv_count = 0
    for i in range(9):
        for j in range(i + 1, 9):
            if puzzle[i] != 0 and puzzle[j] != 0 and puzzle[i] > puzzle[j]:
                inv_count += 1

    # Find blank tile position
    blank_row = 0
    for i, row in enumerate(puzzle):
        if 0 in row:
            blank_row = i
            break

    # Apply solvability condition
    return (inv_count + blank_row) % 2 == 0

def a_star(start):
    goal = ((1, 2, 3), (4, 5, 6), (7, 8, 0))
    if start == goal:
        return []
    visited = set()
    heap = []
    heapq.heappush(heap, (heuristic(start), start, [], 0))
    visited.add(start)
    while heap:
        current = heapq.heappop(heap)
        current_heuristic, current_state, current_path, current_cost = current
        for move, next_state in get_next_states(current_state):
            if next_state == goal:
                return current_path + [move]
            if next_state not in visited:
                new_cost = current_cost + 1
                new_path = current_path + [move]
                new_priority = new_cost + heuristic(next_state)
                heapq.heappush(heap, (new_priority, next_state, new_path, new_cost))
                visited.add(next_state)
    return None

def main():
    puzzle = []
    for _ in range(3):
        row = list(map(int, input().split()))
        puzzle.append(row)
    start_state = tuple(tuple(row) for row in puzzle)
    if not is_solvable(puzzle):
        print("Unsolvable puzzle.")
        return
    solution = a_star(start_state)
    if solution is None:
        print("No solution found.")
    else:
        print(" ".join(solution))

if __name__ == "__main__":
    main()
