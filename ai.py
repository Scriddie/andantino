"""
This file includes the complete game-playing agent class.
"""

from copy import deepcopy
from numpy import inf
import hashlib
import time

# POSSIBLE TODO: build transposition table while opponent is thinking?
class AI:
    """
    Negamax AI
    Calculate moves for a given game
    """
    # TODO: make all the various improvements optional to be able to test them easily
    def __init__(self, game_logic, iterations, player_number, logger, initial_time, use_tt=True):
        self.game_logic = game_logic
        self.game_plan = []  # best sequence, updated as a side effect of evaluation
        self.logger = logger
        self.player_number = player_number
        self.iterations = iterations
        self.iterations_performed = []  # store values for analysis
        self.nodes_visited = []  # store values for analysis
        self.next_move = None
        self.evaluation = None
        self.use_tt = use_tt
        self.t_table = {}
        self.best_move = (9, 9)
        self.initial_time = initial_time  # total time for game
        self.move_start_time = time.time()

    def find_next_move(self, game, time_left):
        """
        Find best next move and update transposition table in the process.
        Adhere to time constraints by clipping search depths accordingly.
        """
        self.iterations_performed = []
        self.nodes_visited = []
        turn = game["turn"]
        self.logger.info(f"\n\nTURN {turn} \n")
        self.move_start_time = time.time()
        for i in range(1, self.iterations+1):
            self.iterations_performed.append(i)
            self.nodes_visited.append(0)
            self.logger.info(f"Iteration: {i}")
            self.max_depth = i
            self.evaluation = self.negamax(game, self.max_depth, alpha=-inf, beta=inf, player_sign=1)
            move_time = time.time() - self.move_start_time
            self.logger.info(f"Move time: {move_time}\n")

            # Panic mode to avoid losing on time
            if (time_left < 10) and (i > 1):
                self.logger.info("-> PANIC CUTOFF\n")
                break

            # Blitz mode: use a constant fraction of time left
            if time_left < self.initial_time/10:
                if time.time() - self.move_start_time > time_left/10:
                    self.logger.info("-> BLITZ CUTOFF\n")
                    break

            if (time.time() - self.move_start_time) > self.initial_time/85:
                break
            
        for key, value in self.t_table.items():
            e = value["value"]
            d = value["depth"]
            f = value["flag"]
            self.logger.info(f"{key}: (evaluation {e}, height {d}, flag '{f}')")
        self.logger.info(f"BEST MOVE: {self.best_move}")
        return self.best_move

    def evaluate(self, game, depth):
        """evaluation of a game, always from the root player's perspective"""
        self.nodes_visited[-1] += 1
        winner = game["winner"]
        if winner != None:
            if winner == self.player_number:
                return 9999999 + depth  # early win -> high depth value (counts down)
            else:
                return -9999999 - depth

        my_connections = 1
        my_cells = 0
        enemy_connections = 1
        enemy_cells = 0
        # my_longest = 1
        # opponent_longest = 1
        # reward continuous lines
        for row in game["grid"]:
            for cell in row:
                if cell["owner"] != None:
                    # idea: count all win directions (sum, not max)
                    # candidate = max(self.game_logic.count_cont_rows(game, cell["row"], cell["col"]))
                    if cell["owner"] == self.player_number:
                        my_cells += 1
                        my_connections += sum(self.game_logic.count_cont_rows(game, cell["row"], cell["col"]))
                        # if (candidate > my_longest): my_longest = candidate
                    else:
                        enemy_cells += 1
                        enemy_connections += sum(self.game_logic.count_cont_rows(game, cell["row"], cell["col"]))
                        # if (candidate > opponent_longest): opponent_longest = candidate
        # # idea: if opponent goes for long lines, play the area game, and vice versa
        eval1 = my_connections/my_cells - enemy_connections/enemy_cells
        # eval2 = my_longest**2 - opponent_longest**2
        # if (eval1 > 0) and (eval2 > 0):  # cautious in winning position
        #     return min(eval1, eval2)
        # if (eval1 < 0) and (eval2 < 0):  # optimistic in losing position
        #     return max(eval1, eval2)
        # else: return eval1 + eval2
        # # return eval1 + eval2
        return eval1

    def order_successors(self, successors):
        """order successors by evaluations from previous iterations"""
        ordered = successors
        ideal_order = []
        successor_state_hashes = [self.game_logic.hash_game(game) for (game, row, col) in successors]
        for hash_value in successor_state_hashes:
            try:
                ideal_order.append(self.t_table[hash_value]["evaluation"])
            except KeyError:
                ideal_order.append(-inf)  # put the ones we have pruned to the very end
            if (len(set(ideal_order)) > 1):  # order it by the first of the tupel pair
                ordered = [x for _, x in sorted(zip(ideal_order, successors), key=lambda pair: pair[0])]
        return ordered

    def negamax(self, game, depth, alpha, beta, player_sign):
        # negamax with ab-pruning and transposition tables
        # alpha: highest max has got so far
        # beta: lowest min has got so far
        # start for player 1: negamax(rootNode, depth, −∞, +∞, 1)
        indent = (self.max_depth - depth +1) * "\t" + "|"

        alphaOrig = alpha
        position_hash = self.game_logic.hash_game(game)

        self.logger.info(f"{indent}Depth: {self.max_depth - depth} -> Hash: {position_hash}")
        # Try retrieving values from transposition table
        if self.use_tt:
            try:
                tt_entry = self.t_table[position_hash]
            except KeyError:
                tt_entry = None
            if (tt_entry != None) and (tt_entry["depth"] >= depth):
                if tt_entry["flag"] == "exact":
                    if self.max_depth == depth:
                        self.best_move = (tt_entry["row"], tt_entry["col"])
                    return tt_entry["value"]
                elif tt_entry["flag"] == "b_cutoff":
                    alpha = max(alpha, tt_entry["value"])
                elif tt_entry["flag"] == "a_cuttoff":
                    beta = min(beta, tt_entry["value"])
                
                if alpha >= beta:
                    return tt_entry["value"]

        # Check for win condition or leaf node
        if (self.game_logic.is_win_condition(game) or (depth == 0)):
            value = player_sign * self.evaluate(game, depth)
            self.logger.info(f"{indent}Evaluation: {value}")
            return value

        successors = self.game_logic.find_successors(game)
        successor_coordinates = [(i, j) for (child, i, j) in successors]
        self.logger.info(f"{indent}SUCCESSORS: {successor_coordinates}")
        successors = self.order_successors(successors)

        value = -inf
        # Traverse game tree in depth first manner
        for child, i, j in successors:
            self.logger.info(f"{indent}-> {i, j}")
            new_value = -self.negamax(child, depth-1, -beta, -alpha, -player_sign)
            if new_value > value:
                self.logger.info(f"{indent}New candidate value at depth {self.max_depth-depth}: {new_value}\n")
                # save best moves on direct successor level
                if self.max_depth == depth:
                    self.best_move = (i, j)
                value = new_value
            alpha = max(alpha, value)
            if alpha >= beta:
                self.logger.info(f"{indent} Pruning")
                break

        # Save newly found value in transposition table
        if self.use_tt:
            new_tt_entry = {"value": value}
            if value <= alphaOrig:
                new_tt_entry["flag"] = "a_cuttoff"
            elif value >= beta:
                new_tt_entry["flag"] = "b_cutoff"
            else:
                new_tt_entry["flag"] = "exact"
            new_tt_entry["depth"] = depth
            new_tt_entry["row"] = i
            new_tt_entry["col"] = j
            self.t_table[position_hash] = new_tt_entry

        return value

