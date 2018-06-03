from chess.pgn import read_game
import chess.svg

from IPython.display import SVG

from pprint import pprint
from typing import List
from flask import Flask

import numpy as np

import requests
import argparse
import cairosvg
import imageio

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

#read_game(StringIO(" ".join(game.pgn)))

parser = argparse.ArgumentParser(description=__doc__)

parser.add_argument("--gameid", dest="gameid",
                    help="game to animate", type=str)
parser.add_argument("--black", dest="black",nargs='?',
                    default=False,const=True,
                    help="which side to view the game from")
parser.add_argument("--css", dest="css", type=argparse.FileType("r"), default="default.css")
parser.add_argument("--output", dest="output", type=str)

settings = parser.parse_args()

result = requests.get(f'https://lichess.org/game/export/{settings.gameid}')

style = settings.css.read() if settings.css else None

game = read_game(StringIO(result.text))
size = 360

with imageio.get_writer(settings.output, mode='I', fps=1) as writer:
    node = game
    while not node.is_end():
        nextNode = node.variation(0)
        board_svg = chess.svg.board(node.board(), coordinates=False, flipped=settings.black, size=size, style=style)
        board_png = imageio.imread(cairosvg.svg2png(bytestring=board_svg))
        writer.append_data(board_png)
        node = nextNode