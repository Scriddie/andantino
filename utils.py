"""
This file includes supplementary methods for logging, analysis of search depth and win rates.
"""

import logging
import os
import time
import numpy.random as npr

def create_logger():
    """start new log file"""
    filename = (f"logs\\andantino.log")
    if os.path.exists(filename):
        os.remove(filename)
    if not os.path.exists("logs"):
        os.mkdir("logs")
    logger = logging.getLogger(filename)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(filename)
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)
    return logger

def remove_logger(logger):
    for i in logger.handlers:
        i.close()
        logger.removeHandler(i)

def check_stats_dir():
    if not os.path.exists("stats"):
        os.mkdir("stats")

def compile_depth_stats(ai_player):
    check_stats_dir()
    filename = "stats/depth_stats.txt"
    with open(filename, "a") as f:
        current_time = str(time.time())
        iteration_nodes = list(zip(ai_player.iterations_performed, ai_player.nodes_visited))
        for iters, nodes in iteration_nodes:
            row = f"{current_time}, {iters}, {nodes}\n"
            f.write(row)

def compile_win_stats(black, white):
    check_stats_dir()
    filename = "stats/win_stats.txt"  
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write(f"time, black_win, white_win\n")
    with open(filename, "a") as f:
        current_time = str(time.time())
        row = f"{current_time}, {str(black)}, {str(white)}\n"
        f.write(row)

