WIDTH = 7
HEIGHT = 6

class Game:

    # cf stands for connected fours, we check a specific line both in a direction and its opposite
    # and count how many cells does a specific player own in this specific line
    cf_check_directions = (
        (0, -1),    # DOWN
        (1, 0),     # RIGHT-LEFT
        (-1, 1),    # UP-LEFT - DOWN-RIGHT
        (1, 1),     # UP-RIGHT - DOWN-LEFT
    )

    
    def __init__(self):
        """ creates a game """
        
        # Setup
        self.game = []
        for _ in range(WIDTH):
            self.game.append([])

        # 0 for player, 1 for computer
        self.turn = 0
        self.connected_four_p0 = 0
        self.connected_four_p1 = 0
        self.moves_played = 0
        self.moves_list = []

    
    def allowed_cell(self, x, y):
        """ checks if a cell is allowed and is filled (since they are built dynamically) """

        if x < 0 or x >= WIDTH:
            return False

        if y < 0 or y >= len(self.game[x]):
            return False
        
        return True

    def play_move(self, move):
        """ Validates if a move is valid then plays it """

        col = self.game[move]
        if len(col) >= HEIGHT:
            raise ValueError("Not allowed move")

        col.append(self.turn)

        gained = 0

        for dx, dy in self.cf_check_directions:
            
            count = 0

            # count in the direction
            x = move 
            y = len(col)-1

            for _ in range(4):

                if not self.allowed_cell(x, y) or self.game[x][y] != self.turn:
                    break

                count += 1
                x += dx
                y += dy

            # count in the opposite direction
            x = move 
            y = len(col)-1

            for _ in range(4):
                if not self.allowed_cell(x, y) or self.game[x][y] != self.turn:
                    break

                count += 1
                x -= dx
                y -= dy
            
            # the total new connected fours is all the current player cells - 3
            # for example if . . . (.) . . and (.) was added, then 6-3 = 3 new connected fours was added
            # current cell is counted twice, so we subtract 4 instead of 

            if count-4 > 0:
                gained += count-4

        if self.turn == 0:
            self.connected_four_p0 += gained
        else:
            self.connected_four_p1 += gained

        self.turn = 1 - self.turn
        self.moves_played += 1
        self.moves_list.append((move, gained))

    def undo_move(self):
        """ Undos a move """

        move, gained = self.moves_list.pop()

        # undo the turn first so the current turn becomes the same turn that originally played the move
        self.turn = 1 - self.turn

        if self.turn == 0:
            self.connected_four_p0 -= gained
        else:
            self.connected_four_p1 -= gained
        
        self.game[move].pop()
        self.moves_played -= 1

    def check_finished(self):
        """ Checks if every cell if full (thus the game has endded) """

        return self.moves_played >= WIDTH * HEIGHT

    def create_copy(self):
        """ Creates a copy of the current game """

        copy = Game()

        for i in range(WIDTH):
            for num in self.game[i]:
                copy.game[i].append(num)
        
        copy.connected_four_p0 = self.connected_four_p0
        copy.connected_four_p1 = self.connected_four_p1
        copy.moves_played = self.moves_played
        copy.turn = self.turn

        for move in self.moves_list:
            copy.moves_list.append(move)

        return copy

    def get_legal_moves(self):
        """Returns valid column indices."""

        order = [3, 2, 4, 1, 5, 0, 6]
        moves = []
        for col in order:
            if len(self.game[col]) < HEIGHT:
                moves.append(col)

        return moves