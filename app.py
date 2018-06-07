from PIL import Image, ImageFont, ImageDraw
from flask import Flask, send_file, request
from tempfile import TemporaryFile
from multiprocessing import Pool
from chess.pgn import read_game
from numpy import array

import chess.svg

import requests
import argparse
import cairosvg
import imageio

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--port", dest="port", default=8080, type=int)
parser.add_argument("--bind", dest="bind", default="0.0.0.0", type=str)
parser.add_argument("--css", dest="css", type=argparse.FileType("r"), default="default.css")

settings = parser.parse_args()

app = Flask(__name__)

style = settings.css.read() if settings.css else None

size = 360

lightgrey = '#8f8f8f'
grey = '#acacac'
darkgrey = '#1a1a1a'
white = '#fff'
black = '#000'


@app.route('/<gameid>.gif', methods=['GET'])
def serve_gif(gameid):
    result = requests.get(f'https://lichess.org/game/export/{gameid}')

    start = time.time()
    game = read_game(StringIO(result.text))
    tempfile = TemporaryFile()

    with imageio.get_writer(tempfile, mode='I', format='gif', subrectangles=True, palettesize=16, fps=0.7) as writer:
        # Add Splash to animation
        splash = create_splash(size, game, gameid)
        [writer.append_data(splash) for i in range(2)]

        # Game
        node = game
        boards = []

        while not node.is_end():
            nextNode = node.variation(0)
            boards.append(node.board())
            node = nextNode

        # perform conversions in parallel
        with Pool(4) as p:
            board_svgs = p.map(board_to_svg, boards)
            board_pngs = p.map(svg_to_png, board_svgs)

        [writer.append_data(imageio.imread(board_png)) for board_png in board_pngs]

        [writer.append_data(splash) for i in range(3)]

    tempfile.seek(0)
    end = time.time()
    print(end - start)

    return send_file(tempfile, mimetype='image/gif')

def svg_to_png(board_svg):
    return cairosvg.svg2png(bytestring=board_svg)

def board_to_svg(board):
    return chess.svg.board(board, coordinates=False, size=size, style=style)

def create_splash(size, game, gameid):
    whitePlayer = game.headers['White']
    blackPlayer = game.headers['Black']

    whiteElo = game.headers['WhiteElo']
    blackElo = game.headers['BlackElo']

    splash = Image.new("RGB", (size,size), color = darkgrey)

    draw = ImageDraw.Draw(splash)
    font = ImageFont.truetype("Merriweather-Bold.ttf", 24)
    lichessfont = ImageFont.truetype("Roboto-Regular.ttf", 30)
    fontcolour = (grey)
    startx = size/8
    starty = size/15
    
    ## Logo
    logo = Image.open('lichess_icon.png', 'r')
    logo = logo.resize((round(size/1.5), round(size/1.5)), resample=Image.BILINEAR)

    splash.paste(logo, (round(size/6), round(size/6)), logo)

    ## Link
    w, h = draw.textsize('lichess.org/'+gameid, font=font)

    draw.text(((size-w)/2 - 10, 300), "lichess", grey, font=lichessfont)
    draw.text(((size-w)/2 - 10 + 95, 300), ".org/"+gameid, lightgrey, font=lichessfont)


    ## Player Text Drop Shadow
    dropShadowDistance = 2

    whiteMsg = '{:} ({:})'.format(whitePlayer, whiteElo)
    w, h = draw.textsize(whiteMsg, font=font)
    draw.text(((size-w)/2 + dropShadowDistance,(size-h)/2 - 20 + dropShadowDistance), whiteMsg, fill=black, font=font)

    blackMsg = '{:} ({:})'.format(blackPlayer, blackElo)
    w, h = draw.textsize(blackMsg, font=font)
    draw.text(((size-w)/2 + dropShadowDistance,(size-h)/2 + 20 + dropShadowDistance), blackMsg, fill=black, font=font)

    ## Player Text
    whiteMsg = '{:} ({:})'.format(whitePlayer, whiteElo)
    w, h = draw.textsize(whiteMsg, font=font)
    draw.text(((size-w)/2,(size-h)/2 - 20), whiteMsg, fill=white, font=font)

    blackMsg = '{:} ({:})'.format(blackPlayer, blackElo)
    w, h = draw.textsize(blackMsg, font=font)
    draw.text(((size-w)/2,(size-h)/2 + 20), blackMsg, fill=white, font=font)

    return array(splash)


if __name__ == '__main__':
    app.run(host=settings.bind, port=settings.port)