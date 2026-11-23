WIDTH = 7
HEIGHT = 6

class Game:

    # cf stands for connected fours, we check a specific line both in a direction and its opposite
    # and count how many cells does a specific player own in this specific line
    cf_check_directions = (
        (0, -1),    # DOWN
        (1, 0),     # RIGHT-LEFT
        (-1, 1),    # UP-LEFT - DOWN-RIGHT
        (1, 1),    # UP-RIGHT - DOWN-LEFT
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
                if self.turn == 0:
                    self.connected_four_p0 += count-4

                else:
                    self.connected_four_p1 += count-4                

        self.turn = 1 - self.turn
        self.moves_played += 1
    

    def check_finished(self):
        """ Checks if every cell if full (thus the game has endded) """

        return self.moves_played >= WIDTH * HEIGHT