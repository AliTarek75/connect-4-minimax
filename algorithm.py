from heuristics import heuristic


def cache_state(game,depth,k):
    cols = tuple(tuple(col) for col in game.game)
    level = k - depth
    return (
        cols,
        game.turn,
        game.connected_four_p0,
        game.connected_four_p1,
        level,
    )

def get_best_move(game, k):

    copy = game.create_copy()
    table = {}
    best = max_value(copy, k, 0, -float('inf'), float('inf'), table)

    return best

def max_value(game, k, depth, alpha, beta, table):
    if depth == k or game.check_finished():
        return heuristic(game), None

    key = cache_state(game,depth,k)
    if key in table:
        return table[key]

    val = -float('inf')
    best_move = -1
    pruned = False

    for move in game.get_legal_moves():
        game.play_move(move)
        node_value, _  = min_value(game, k, depth+1, alpha, beta, table)
        game.undo_move()

        if node_value > val:
            val = node_value
            best_move = move

        if val > alpha:
            alpha = val

        if alpha >= beta:
            pruned = True
            break

    if not pruned:
        table[key] = (val,best_move)
    return val, best_move

def min_value(game, k, depth, alpha, beta, table):
    if depth == k or game.check_finished():
        return heuristic(game), None

    key = cache_state(game,depth,k)
    if key in table:
        return table[key]

    val = float('inf')
    best_move = -1
    pruned = False

    for move in game.get_legal_moves():
        game.play_move(move)

        node_value, _ = max_value(game, k, depth+1, alpha, beta, table)
        game.undo_move()
        if node_value < val:
            val = node_value
            best_move = move

        if val < beta:
            beta = val

        if alpha >= beta:
            pruned = True
            break
        
    if not pruned:
        table[key] = (val,best_move)
    return val, best_move
