"""idea: create UI that can take up a given stored game and plot it"""

from math import pi, cos, sin, sqrt
from copy import deepcopy

class View:
    """This class provides most of the information needed for the graphical
    representation of the game. It detects user input and triggers game actions
    accordingly."""
    def __init__(self, game_logic, game, vertex_count=6, radius=20):
        self.vertex_count = vertex_count
        self.radius = radius
        self.game_logic = game_logic  # ui has a game_logic to query the game
        self.game = game  # ui has a game it keeps track off
        # cell_positions can be traversed with same indexes as game_grid
        self.cell_positions = self.find_cell_positions(game)
        self.text_pos = self.find_cell_text_pos(self.cell_positions)
        self.text = self.update_text()

    def update_text(self):
        """Text information about whose turn it is"""
        # TODO: the text pieces should be provided by the game logic class to make them work for console as well!
        if self.game_logic.get_winner(self.game) != None:
            # player who put the last stone wins
            return f"{'White' if self.game_logic.get_player(self.game) == 0 else 'Black'} WINS!"
        else:
            return f"{'White' if self.game_logic.get_player(self.game) == 1 else 'Black'} to move"

    def update_text_on_move(self, legal_move):
        """Text information in case of illegal moves"""
        if legal_move:            
            self.text = self.update_text()
        else:
            player = self.game_logic.get_player(self.game)
            self.text = f"Illegal move by {'White' if player == 1 else 'Black'}"

    def get_text(self):
        """text information about state of game"""
        return self.text

    def draw_regular_polygon(self, position):
        """draw a hexagon with given radius"""
        # position is center of polygon
        n, r = self.vertex_count, self.radius
        x, y = position
        return([
            (x + r * cos(2 * pi * i / n + pi/n),
            y + r * sin(2 * pi * i / n + pi/n))
            for i in range(n)
        ])

    def find_cell_positions(self, game):
        """Determine cell positions for initial drawing of the board"""
        grid = game["grid"]
        position_grid = []
        for i in grid:
            new_row = []
            for cell in i:
                row, col = cell["row"], cell["col"]
                x = 250
                y = 100
                side_length = 10
                x = x + row * 2*self.radius - col * self.radius
                y = y + col * 1.75*self.radius
                if row >= side_length:
                    x = x - (row-side_length+1) * self.radius
                    y = y + (row-side_length+1) * 1.75*self.radius
                position = (x, y)
                new_row.append(position)
            position_grid.append(new_row)
        return position_grid

    def get_player_buttons(self):
        """Draw buttons for choosing a player"""
        all_buttons = []
        all_buttons.append(((0, 0, 0), [(900, 200), (800, 200), (800, 300), (900, 300)]))
        all_buttons.append(((255, 255, 255),       [(1000, 200), (900, 200), (900, 300), (1000, 300)]))
        return all_buttons

    def detect_player(self, mouse_pos):
        """Trigger player change on button click"""
        button_pos_lists = [i[1] for i in self.get_player_buttons()]
        for i, pos_list in enumerate(button_pos_lists):
            if ((mouse_pos[0] < pos_list[0][0]) and 
                (mouse_pos[0] > pos_list[1][0]) and
                (mouse_pos[1] < pos_list[2][1]) and
                (mouse_pos[1] > pos_list[1][1])):
               self.player = i
               return i
        return None

    def detect_cell(self, mouse_pos):
        """Detect the cell (tile) a player has clicked on"""
        for i, row in enumerate(self.cell_positions):
            for j, cell in enumerate(row):
                x, y = self.cell_positions[i][j]
                distance = sqrt(abs(mouse_pos[0] - x)**2 + abs(mouse_pos[1] - y)**2)
                if distance < self.radius:
                    return(i, j)
        return None

    def find_cell_text_pos(self, cell_positions):
        """Determine positions for alphanumeric cell coordinates"""
        text_pos = []
        for row in cell_positions:
            new_row = []
            for pos in row:
                new_pos = (pos[0] - self.radius/2, pos[1])
                new_row.append(new_pos)
            text_pos.append(new_row)
        return text_pos

    def get_cell_text_pos(self):
        return self.text_pos

    def draw_coordinates(self):
        all_coordinates = []
        for i, row in enumerate(self.get_cell_text_pos()):
            for j, cell_pos in enumerate(row):
                pos = self.game_logic.indexes_to_coordinates(i, j)
                coordinates = str(pos[0])+str(pos[1])
                all_coordinates.append((coordinates, cell_pos))
        return all_coordinates

    def draw_grid(self):
        all_cells = []
        for i, row in enumerate(self.cell_positions):
            for j, position in enumerate(row):
                coordinates = self.draw_regular_polygon(position)
                cell_owner = self.game_logic.get(self.game, i, j)["owner"]
                if cell_owner == None:
                    color = (255,222,173)
                elif cell_owner == 0:
                    color = (0, 0, 0)
                else:
                    color = (255, 255, 255)
                all_cells.append((color, coordinates))            
        return(all_cells)

    def get_time_info(self, player_number):
        if player_number == 0:
            return(f"Black: {round(self.game_logic.player_0_time)}")
        elif player_number == 1:
            return(f"White: {round(self.game_logic.player_1_time)}")
        else:
            raise IndexError

    def detect_revert_action(self, mouse_pos):
        color, pos_list = self.get_return_button()
        if ((mouse_pos[0] < pos_list[0][0]) and 
            (mouse_pos[0] > pos_list[1][0]) and
            (mouse_pos[1] < pos_list[2][1]) and
            (mouse_pos[1] > pos_list[1][1])):
            return True
        return False

    def get_return_button(self):
        return((0, 0, 255), [(900, 600), (800, 600), (800, 650), (900, 650)])

