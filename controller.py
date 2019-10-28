"""
This file contains the game loop, instantiation of the game_logic and game_playing agent.
"""

import ai
import game_logic
import logging
import pygame
import pygame.freetype
import time
import ui
import utils
from copy import deepcopy
from importlib import reload

# reload to load changes as well
reload(game_logic)
reload(ui)
reload(ai)
reload(utils)

# constants
COMPILE_STATISTICS = True  # log nodes visited and win statistics in stats dir
TIME_LIMIT = 600  # in sec, should be 600
ITERATIONS_1 = 15
ITERATIONS_2 = 15
GAME_STACK = []

game_logic = game_logic.GameLogic(TIME_LIMIT)
game = game_logic.create_game()
view = ui.View(game_logic, game)
p1 = ai.AI(game_logic, ITERATIONS_1, player_number=0, logger=utils.create_logger(), initial_time=game_logic.initial_time, use_tt=True)  # black
p2 = None  # p2 = ai.AI(game_logic, ITERATIONS_2, player_number=1, logger=utils.create_logger(), initial_time=game_logic.initial_time)  # white
start_time = time.time()

game_over = False
pygame.init()
screen = pygame.display.set_mode((1200, 900))
pygame.display.set_caption("Andantino")
pygame.freetype.init()
GAME_FONT = pygame.freetype.SysFont("Ubuntu Mono", 24)
POS_FONT = pygame.freetype.SysFont("Ubuntu Mono", 9)
display_text = view.get_text()
game_loop_counter = 0  

if COMPILE_STATISTICS:
    utils.check_stats_dir()
    with open("stats/depth_stats.txt", "w") as f:
        f.write(f"time, iterations, nodes_visited\n")   

while not game_over:
    game_loop_counter = 0
    screen.fill((50, 50, 50))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_over = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            new_human_player = view.detect_player(mouse_pos)
            if new_human_player != None:
                p1.player_number = (new_human_player+1)%2
            cell = view.detect_cell(mouse_pos)

            if view.detect_revert_action(mouse_pos):
                view.game = GAME_STACK[-2]
                p1.game = GAME_STACK[-2]
                game = GAME_STACK[-2]
                GAME_STACK = GAME_STACK[0:-2]

            # Human player places a stone
            if cell != None:
                game_logic.update_time(game, time.time() - start_time)
                row, col = cell
                GAME_STACK.append(deepcopy(game))
                legal_move = game_logic.update_owner(game, row, col)
                view.update_text_on_move(legal_move)
                start_time = time.time()
                game_loop_counter = 1
                
    # do AI action
    def ai_action(player):
            start_time = time.time()
            ai_move = player.find_next_move(game, time_left=game_logic.get_time(player.player_number))
            game_logic.update_time(game, time.time() - start_time)  # time in seconds
            GAME_STACK.append(deepcopy(game))
            legal_move = game_logic.update_owner(game, ai_move[0], ai_move[1])
            view.update_text_on_move(legal_move)
            start_time = time.time()

    if ((game_loop_counter == 0) and (game_logic.get_player(game) == p1.player_number)
     and (game_logic.get_winner(game) == None)):
        ai_action(p1)  # black
        if COMPILE_STATISTICS:
            utils.compile_depth_stats(p1)

    if p2 != None and ((game_loop_counter == 0) and (game_logic.get_player(game) == p2.player_number)
     and (game_logic.get_winner(game) == None)):
        ai_action(p2)  # white
            
    display_text = view.get_text()

    # choose player
    GAME_FONT.render_to(screen, (800, 150), "Pick a color for the non-AI player:", (255, 255, 255))
    for button in view.get_player_buttons():
        color, pos = button
        pygame.draw.polygon(screen, color, pos)
    
    # text information
    GAME_FONT.render_to(screen, (800, 100), display_text, (255, 0, 0))
    latest_ai_move = game_logic.indexes_to_coordinates(*p1.best_move)
    GAME_FONT.render_to(screen, (800, 350), f"AI move: {latest_ai_move}", (255, 255, 255))
    GAME_FONT.render_to(screen, (800, 700), view.get_time_info(p1.player_number), (255, 255, 255))

    # revert button
    color, pos = view.get_return_button()
    pygame.draw.polygon(screen, color, pos)
    GAME_FONT.render_to(screen, (pos[1][0], pos[1][1]), "REVERT", (255, 255, 255))

    # hexagonal grid
    for cell in view.draw_grid():
        color, coordinates = cell
        pygame.draw.polygon(screen, color, coordinates)

    # coordinate notation
    for position in view.draw_coordinates():
        coordinate, cell_pos = position
        POS_FONT.render_to(screen, cell_pos, coordinate, (255, 0, 0))
    
    pygame.display.flip()

pygame.quit()

utils.remove_logger(p1.logger)
if p2 != None:
    utils.remove_logger(p2.logger)
logging.shutdown()

if COMPILE_STATISTICS:
    if game["winner"] != None:
        black_points = 1 if game["winner"] == 0 else 0
        white_points = 1 if game["winner"] == 1 else 0
        utils.compile_win_stats(black_points, white_points)

