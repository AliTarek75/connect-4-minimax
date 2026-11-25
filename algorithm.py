import time

nodes = []
def save(depth, move, value, alpha, beta, is_max, is_leaf):
    nodes.append({
        'depth':   depth,
        'move':    move,
        'value':   value,
        'alpha':   alpha,
        'beta':    beta,
        'is_max':  is_max,
        'is_leaf': is_leaf,
        'pruned':  False,
    })


def get_best_move(game, k):
    nodes.clear()
    copy = game.create_copy()

    start = time.time()
    val, best_move = max_value(copy, k, 0, -float('inf'), float('inf'))
    elapsed = time.time() - start

    return val, best_move, elapsed


def max_value(game, k, depth, alpha, beta):
    if depth == k or game.check_finished():
        return game.heuristic(), None

    val = -float('inf')
    best_move = -1

    for move in game.get_legal_moves():
        game.play_move(move)
        node_value, _ = min_value(game, k, depth + 1, alpha, beta)

        save(depth=depth + 1,
             move=move,
             value=node_value,
             alpha=alpha,
             beta=beta,
             is_max=False,
             is_leaf=depth + 1 == k or game.check_finished()
        )

        game.undo_move()

        if node_value > val:
            val = node_value
            best_move = move

        alpha = max(alpha, val)
        if alpha >= beta:
            nodes[-1]['pruned'] = True
            break

    return val, best_move


def min_value(game, k, depth, alpha, beta):
    if depth == k or game.check_finished():
        return game.heuristic(), None

    val = float('inf')
    best_move = -1

    for move in game.get_legal_moves():
        game.play_move(move)
        node_value, _ = max_value(game, k, depth + 1, alpha, beta)

        save(depth=depth + 1,
             move=move,
             value=node_value,
             alpha=alpha,
             beta=beta,
             is_max=True,
             is_leaf=depth + 1 == k or game.check_finished()
        )

        game.undo_move()

        if node_value < val:
            val = node_value
            best_move = move

        beta = min(beta, val)
        if alpha >= beta:
            nodes[-1]['pruned'] = True
            break

    return val, best_move