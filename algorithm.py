from heuristics import temp_heuristic

def get_best_move(game, k):

    copy = game.create_copy()
    best = max_value(copy, k, 0, -float('inf'), float('inf'))

    return best

def max_value(game, k, depth, alpha, beta):
    if depth == k or game.check_finished():
        return temp_heuristic(game), None

    val = -float('inf')
    best_move = -1

    for move in game.get_legal_moves():
        game.play_move(move)

        node_value, _  = min_value(game, k, depth+1, alpha, beta)

        game.undo_move()

        if node_value > val:
            val = node_value
            best_move = move

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break
    
    return val, best_move

def min_value(game, k, depth, alpha, beta):
    if depth == k or game.check_finished():
        return temp_heuristic(game), None

    val = float('inf')
    best_move = -1

    for move in game.get_legal_moves():
        game.play_move(move)

        node_value, _ = max_value(game, k, depth+1, alpha, beta)

        game.undo_move()

        if node_value < val:
            val = node_value
            best_move = move

        if val < beta:
            beta = val

        if alpha >= beta:
            break

    return val, best_move

    