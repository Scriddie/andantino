import logging
import os
import time
import numpy.random as npr

def create_logger():
    """start new log file"""
    filename = (f"logs\\andantino{npr.random()}.log")
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

def compile_stats(black, white):
    filename = "stats.txt"
    if os.path.exists(filename):
        with open(filename, "a") as f:
            current_time = str(time.time())
            row = f"{current_time}, {str(black)}, {str(white)}\n"
            f.write(row)

