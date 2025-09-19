# player.py
class Player:
    def __init__(self, x, y, controls):
        self.x = x
        self.y = y
        self.controls = controls
        self.holding = None

    def move(self, dx, dy, board):
        new_x = self.x + dx
        new_y = self.y + dy
        if board.is_walkable(new_x, new_y):
            self.x = new_x
            self.y = new_y

    def interact(self, board):
        cell = board.get_cell(self.x, self.y)

        if self.holding is None and cell == 2:
            self.holding = "tomate"
            board.set_cell(self.x, self.y, 0)
        elif self.holding and cell == 4:
            item = self.holding
            self.holding = None
            return ("deliver", item)
        return None
