# inspiration (aka pseudocode) taken from https://en.wikipedia.org/wiki/Negamax

from copy import deepcopy
from numpy import inf
import hashlib
import time

# TODO: trivial speed up for white: place random
# TODO: incentivise AI to fight on for as long as possible!
# POSSIBLE TODO: build transposition table while opponent is thinking?
class AI:
    """
    Negamax AI
    Calculate moves for a given game
    """
    # TODO: make all the various improvements optional to be able to test them easily
    def __init__(self, game_logic, iterations, player_number, logger):
        self.game_logic = game_logic
        self.game_plan = []  # best sequence, updated as a side effect of evaluation
        self.logger = logger
        self.player_number = player_number
        self.iterations = iterations
        self.next_move = None
        self.evaluation = None
        self.move_time = 0
        self.t_table = {}
        self.best_move = (9, 9)

    def find_next_move(self, game, time_left):
        """find best next move and update transposition table in the process"""
        turn = game["turn"]
        self.logger.info(f"\n\nTURN {turn} \n")
        for i in range(1, self.iterations+1):
            self.logger.info(f"Iteration: {i}")
            self.max_depth = i
            start_time = time.time()
            self.evaluation = self.negamax(game, self.max_depth, alpha=-inf, beta=inf, player_sign=1)
            self.move_time = time.time() - start_time
            self.logger.info(f"Move time: {self.move_time}\n")
            if (time_left < 10) and (i > 1):  # panic mode
                self.logger.info("-> PANIC CUTOFF\n")
                break
            if self.move_time > time_left/100:  # rapid mode
                self.logger.info("-> BLITZ CUTOFF\n")
                break
            
        for key, value in self.t_table.items():
            e = value["value"]
            d = value["depth"]
            f = value["flag"]
            self.logger.info(f"{key}: (evaluation {e}, height {d}, flag '{f}')")
        self.logger.info(f"BEST MOVE: {self.best_move}")
        return self.best_move

    def evaluate(self, game):
        """evaluation of a game, always from the root player's perspective"""
        # TODO: maybe reward play in the center of the board?
        winner = game["winner"]
        if winner != None:
            if winner == self.player_number:
                return 9999
            else:
                return -9999

        my_longest = 1
        opponent_longest = 1
        # reward continuous lines
        for row in game["grid"]:
            for cell in row:
                if cell["owner"] != None:
                    candidate = max(self.game_logic.count_cont_rows(game, cell["row"], cell["col"]))
                    if (candidate > my_longest) and (cell["owner"] == self.player_number):
                        my_longest = candidate
                    elif (candidate > opponent_longest) and (cell["owner"] != self.player_number):
                        opponent_longest = candidate
        return my_longest**2 - opponent_longest**2

    def order_successors(self, successors):
        """order successors by evaluations from previous iterations"""
        # TODO: check if this is actually an improvement
        # am I looking at moves from the right perspective at all??
        ordered = successors
        ideal_order = []
        successor_state_hashes = [self.game_logic.hash_game(game) for (game, row, col) in successors]
        for hash_value in successor_state_hashes:
            try:
                ideal_order.append(self.t_table[hash_value]["evaluation"])
            except KeyError:
                ideal_order.append(-inf)  # put the ones we have pruned to the very end
            # TODO: come up with some sensible logging
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

        if self.game_logic.is_win_condition(game) or depth == 0:
            value = player_sign * self.evaluate(game)
            self.logger.info(f"{indent}Evaluation: {value}")
            return value

        successors = self.game_logic.find_successors(game)
        successor_coordinates = [(i, j) for (child, i, j) in successors]
        self.logger.info(f"{indent}SUCCESSORS: {successor_coordinates}")
        successors = self.order_successors(successors)

        value = -inf

        for child, i, j in successors:
            self.logger.info(f"{indent}-> {i, j}")
            new_value = -self.negamax(child, depth-1, -beta, -alpha, -player_sign)
            if new_value > value:
                self.logger.info(f"{indent}New candidate value at depth {self.max_depth-depth}: {new_value}\n")
                if self.max_depth == depth:  # save best moves on highest level
                    self.best_move = (i, j)
                value = new_value
            alpha = max(alpha, value)
            if alpha >= beta:
                self.logger.info(f"{indent} Pruning")
                break

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

