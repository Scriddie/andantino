import logging
import os

def create_logger():
    """start new log file"""
    if os.path.exists("andantino.log"):
        os.remove("andantino.log")
    logger = logging.getLogger("andantino.log")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler('andantino.log')
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)
    return logger

def remove_logger(logger):
    for i in logger.handlers:
        i.close()
        logger.removeHandler(i)
