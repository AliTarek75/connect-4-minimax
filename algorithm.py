from heuristics import temp_heuristic

def get_best_move(game, k):

    copy = game.create_copy()

    best = max_value(copy, k, 0)

    return best

def max_value(game, k, depth):
    if depth == k or game.check_finished():
        return temp_heuristic(game), None

    val = -float('inf')
    best_move = -1

    for move in game.get_legal_moves():
        game.play_move(move)

        node_value, _  = min_value(game, k, depth+1)
        if node_value > val:
            val = node_value
            best_move = move
        
        game.undo_move()
    
    return val, best_move

def min_value(game, k, depth):
    if depth == k or game.check_finished():
        return temp_heuristic(game), None

    val = float('inf')
    best_move = -1

    for move in game.get_legal_moves():
        game.play_move(move)

        node_value, _ = max_value(game, k, depth+1)
        if node_value < val:
            val = node_value
            best_move = move
        
        game.undo_move()

    return val, best_move

    