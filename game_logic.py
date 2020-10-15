"""
This class contains the game logic including rules, win conditions and manipulations of the game state.
"""

from operator import add
from copy import deepcopy
import hashlib


class GameLogic:
    """GameLogic class can perform game operations on any game"""
    def __init__(self, time_limit):
        self.BOARD_SIZE = 19
        self.NUMBER_COORDINATES = list(range(1, 20))
        self.LETTER_COORDINATES = ["A", "B", "C", "D", "E", "F", "G", "H",
         "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S"]
        self.initial_time = time_limit
        self.player_0_time = time_limit
        self.player_1_time = time_limit

    def create_cell(self, row, col):
        return {
            "row": row,
            "col": col,
            "owner": None,
            "checked": False
        }

    def create_game(self):
        game = {
            "grid": self.create_grid(),
            "turn": 0,
            "winner": None
        }
        self.update_owner(game, row=9, col=9)
        return game

    def create_grid(self):
        grid = []

        upper_half = list(range(10, 20))  # lengths of sub_lists in upper half
        for row, row_index in enumerate(upper_half):
            new_row = []    
            for col in range(row_index):
                new_row.append(self.create_cell(row, col))
            grid.append(new_row)

        lower_half = list(range(10, 19))
        lower_half.reverse()
        for row, row_length in enumerate(lower_half):
                new_row = []
                for col in range(row_length):
                    # letter_coord, number_coord = self.indexes_to_coordinates(row+10, col)
                    new_row.append(self.create_cell(row+10, col))
                    # new_row.append(cell_logic.Cell(row+10, col, letter_coord, number_coord))
                grid.append(new_row)
        
        return(grid) 

    def indexes_to_coordinates(self, row, col):
        """Turn coordinate notation into list indexes for game grid"""
        if row <= 9:
            letter_coord = self.LETTER_COORDINATES[row]
            number_coord = self.NUMBER_COORDINATES[col]
            return(letter_coord, number_coord)
        else:
            letter_coord = self.LETTER_COORDINATES[row]
            number_coord = self.NUMBER_COORDINATES[col + (row - 9)]
            return(letter_coord, number_coord)

    def update_owner(self, game, row, col):
        player = self.get_player(game)
        if self.is_legal(game, row, col):
            self.get(game, row, col)["owner"] = self.get_player(game)
            if self.is_win_condition(game):
                game["winner"] = player
            self.next_turn(game)
            return True
        else:
            return False

    def get_neighbours(self, game, row, col):
        neighbour_indexes = [(-1, -1), (0, -1), (1, 0), (1, 1), (0, 1), (-1, 0)]
        neighbours = []
        for x, y in neighbour_indexes:  # identify all neighbours
            neighbour_x = row + x
            neighbour_y = col + y
            if (row >= 9) and (neighbour_x > row):
                neighbour_y -= 1
            if (row >= 10) and (neighbour_x < row):
                neighbour_y += 1
            if neighbour_x >= 0 and neighbour_y >= 0:
                try:
                    new_neighbour = self.get(game, neighbour_x, neighbour_y)
                except IndexError:
                    new_neighbour = None
            else:
                new_neighbour = None
            neighbours.append(new_neighbour)
        return neighbours

    def is_legal(self, game, row, col):  # this should be a GameLogic method
        """check if a specific cell can be occupied"""
        real_neighbours = [i for i in self.get_neighbours(game, row, col) if (i != None)]
        occupied_neighbours = sum([1 if i["owner"]!=None else 0 for i in real_neighbours])
        if ((self.get(game, row, col)["owner"] == None) and
                ((occupied_neighbours >= 2) or
                    ((game["turn"] == 1) and (occupied_neighbours >= 1)) or 
                    (game["turn"] == 0))):
            return True
        else:
            return False

    def find_successors(self, game):
        """find all legal successor games"""
        grid = game["grid"]
        successors = []
        for i, row in enumerate(grid):
            for j, cell in enumerate(row):
                if self.is_legal(game, cell["row"], cell["col"]):
                    new_game = deepcopy(game)
                    self.update_owner(new_game, i, j)
                    successors.append((new_game, i, j))
        return successors

    def continue_row(self, game, row, col, index, owner):
        """continue counting into a given direction"""
        cell = self.get(game, row, col)
        ind_nb = self.get_neighbours(game, row, col)[index]
        if (cell["owner"] == None) or (cell["owner"] != owner) or (ind_nb == None):
            return 0
        elif (ind_nb["owner"] == cell["owner"]) and (cell["owner"] == owner):
            return 1 + self.continue_row(game, ind_nb["row"], ind_nb["col"], index, owner)
        elif cell["owner"] == owner:
            return 1
        else:
            raise IndexError("case in 'continue_row' not anticipated")

    def count_cont_rows(self, game, row, col):
        """count win directions for a given cell"""
        cell = self.get(game, row, col)
        neighbours = self.get_neighbours(game, row, col)
        cont_rows = [0, 0, 0, 0, 0, 0]
        win_directions = [0, 0, 0]
        for i, nb in enumerate(neighbours):
            if nb != None:
                cont_rows[i] = 1 + self.continue_row(game, nb["row"], nb["col"], i, cell["owner"])
            else:
                cont_rows[i] = 1
        win_directions[0] = cont_rows[0] + cont_rows[3] - 1  # dont count this cell twice
        win_directions[1] = cont_rows[1] + cont_rows[4] - 1
        win_directions[2] = cont_rows[2] + cont_rows[5] - 1
        return win_directions

    def is_row_win(self, game):
        """find row wins in given game"""
        grid = game["grid"]
        for row in grid:
            for cell in row:
                if cell["owner"] != None:
                    win_directions = self.count_cont_rows(game, cell["row"], cell["col"])
                    if max(win_directions) >= 5:
                        return(True)
        return False

    
    def is_enclosed(self, game, row, col, owner):
        cell = self.get(game, row, col)
        cell["checked"] = True
        neighbours = self.get_neighbours(game, row, col)
        if (cell["owner"] != owner) and (cell["owner"] != None):
            # This cell is a neighbour of enemy colour
            return True
        else:
            if None in neighbours:
                # border cell
                return False
            else:  
                # neighbour is either unoccupied or of same color
                enclosed = True  # enclosed until proven otherwise
                for nb in neighbours:
                    if not nb["checked"]:
                        enclosed = enclosed and self.is_enclosed(game, 
                            nb["row"], nb["col"], owner)
                return enclosed


    def uncheck(self, game):
        """uncheck all cells in given game"""
        grid = game["grid"]
        for row in grid:
            for cell in row:
                cell["checked"] = False

    def is_enclosure_win(self, game):
        """find enclosure wins in given game"""
        grid = game["grid"]
        for row in grid:
            for cell in row:
                if cell["owner"] != None:
                    self.uncheck(game)
                    if self.is_enclosed(game, cell["row"], cell["col"], cell["owner"]):
                        return True
        self.uncheck(game)
        return False

    def is_win_condition(self, game):
        """updates and returns win information"""
        return (self.is_row_win(game) or self.is_enclosure_win(game))

    def get_winner(self, game):
        return game["winner"]

    def get(self, game, row, col):
        """returns a specific cell"""
        return(game["grid"][row][col])

    def next_turn(self, game):
        game["turn"] += 1

    def get_player(self, game):
        return game["turn"] % 2  # {0: black, 1: white}   

    def hash_game(self, game):
        """find a hash unique to the grid configuration"""
        game_backbone = []
        for row in game["grid"]:
            new_row = []
            for cell in row:
                new_row.append(cell["owner"])
            game_backbone.append(new_row)
        return hash(str(game_backbone))

    def update_time(self, game, time):
        # time management should probably be part of the controller
        if self.get_player(game) == 0:
            self.player_0_time -= time
        elif self.get_player(game) == 1:
            self.player_1_time -= time
        else:
            raise IndexError

    def get_time(self, player_number):
        if player_number == 0:
            return self.player_0_time
        elif player_number == 1:
            return self.player_1_time
        else:
            raise IndexError
