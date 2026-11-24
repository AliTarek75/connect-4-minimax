from game import WIDTH, HEIGHT

DIRECTIONS = ((1, 0), (0, 1), (1, 1), (1, -1))


def score_diff(game):
    diff = game.connected_four_p1 - game.connected_four_p0
    return diff


def possible_score(game):
    ai_possible = 0
    human_possible = 0

    for x in range(WIDTH):
        for y in range(HEIGHT):
            for dx, dy in DIRECTIONS:
                end_x = x + 3 * dx
                end_y = y + 3 * dy
                if not (0 <= end_x < WIDTH and 0 <= end_y < HEIGHT):
                    continue

                has_ai = False
                has_human = False
                cx, cy = x, y

                for _ in range(4):
                    c_col = game.game[cx]
                    cell = c_col[cy] if cy < len(c_col) else None

                    if cell == 1:
                        has_ai = True
                    elif cell == 0:
                        has_human = True

                    if has_human and has_ai:
                        break

                    cx += dx
                    cy += dy

                if not has_human:
                    ai_possible += 1
                if not has_ai:
                    human_possible += 1

    return ai_possible - human_possible


def heuristic(game):
    return possible_score(game) + 100 * score_diff(game)
