# pre computations

WIDTH = 7
HEIGHT = 6

# computes the move ordering from the middle outwards
mid = WIDTH // 2
MOVE_ORDER = [mid]
for offset in range(1, WIDTH):
    if mid - offset >= 0:
        MOVE_ORDER.append(mid - offset)
    if mid + offset < WIDTH:
        MOVE_ORDER.append(mid + offset)

# computes every possible 4-cell window and maps every cell to all the windows that pass through that cell
ALL_WINDOWS = []

# we check a specific line both in a direction and its opposite
DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))

for x in range(WIDTH):
    for y in range(HEIGHT):
        for dx, dy in DIRECTIONS:
            ex, ey = x + 3 * dx, y + 3 * dy
            if 0 <= ex < WIDTH and 0 <= ey < HEIGHT:
                window = tuple((x + i * dx, y + i * dy) for i in range(4))
                ALL_WINDOWS.append(window)

CELL_WINDOWS = {}
for x in range(WIDTH):
    for y in range(HEIGHT):
        CELL_WINDOWS[(x, y)] = [w for w in ALL_WINDOWS if (x, y) in w]

class Game:

    # the weights for specific progressed 4-cell window, and specifically to how much progress it has (for heurisitcs)
    window_weights = (0.0, 0.01, 0.1, 0.4)

    
    def __init__(self):
        """ creates a game """
        
        # Setup
        self.game = []
        for _ in range(WIDTH):
            self.game.append([])

        # 0 for player, 1 for computer
        self.turn = 0
        self.connected_four = [0, 0]
        self.moves_played = 0
        self.ai = 1
        self.moves_list = []

        # counts the difference of every single window of 4 that is can be a possible connected 4, weighted by how close it is 
        self.window_score_diff = 0

    def play_move(self, move):
        """ Validates if a move is valid then plays it """

        col = self.game[move]
        if len(col) >= HEIGHT:
            raise ValueError("Not allowed move")

        col.append(self.turn)

        gained = 0
        total_window_change = 0.0
        x = move
        y = len(col) - 1

        # we go over all the windows that pass through the cell that was played
        for window in CELL_WINDOWS[(x, y)]:
            count_mine = 0
            count_enemy = 0

            # go over every cell in the window
            for wx, wy in window:
                col = self.game[wx]
                if wy < len(col):
                    if col[wy] == self.turn:
                        count_mine += 1
                    else:
                        count_enemy += 1

            # new full connect four completed in this window
            if count_mine == 4:
                gained += 1

            # enemy lost a progreesed window
            if count_mine == 1:
                total_window_change += self.window_weights[count_enemy] if self.turn == 1 else -1 * self.window_weights[count_enemy]
            
            # progressed an unblocked window
            if count_enemy == 0:
                
                # not counting full connected fours
                new = self.window_weights[count_mine] if count_mine < 4 else 0

                change = new - self.window_weights[count_mine - 1]
                total_window_change += change if self.turn == 1 else -change

        self.connected_four[self.turn] += gained
        self.window_score_diff += total_window_change
        self.turn = 1 - self.turn
        self.moves_played += 1
        self.moves_list.append((move, gained, total_window_change))


    def undo_move(self):
        """ Undos a move """

        move, gained, total_window_change = self.moves_list.pop()

        # undo the turn first so the current turn becomes the same turn that originally played the move
        self.turn = 1 - self.turn

        self.connected_four[self.turn] -= gained
        self.window_score_diff -= total_window_change
        self.game[move].pop()
        self.moves_played -= 1


    def heuristic(self):
        """returns the heuristic of the current stats, it combines actual score difference + weighted potential difference."""

        sign = 1 if self.ai == 1 else -1
        return sign * ((self.connected_four[1] - self.connected_four[0]) + self.window_score_diff)

    def check_finished(self):
        return self.moves_played >= WIDTH * HEIGHT

    def get_legal_moves(self):
        """Returns valid column indices."""

        moves = []
        for col in MOVE_ORDER:
            if len(self.game[col]) < HEIGHT:
                moves.append(col)

        return moves

    def create_copy(self):
        """ Creates a copy of the current game """

        copy = Game()
        copy.ai = self.ai 
        copy.game = [list(col) for col in self.game]
        copy.connected_four = list(self.connected_four)
        copy.window_score_diff = self.window_score_diff
        copy.moves_played = self.moves_played
        copy.turn = self.turn
        copy.moves_list = list(self.moves_list)
        
        return copy