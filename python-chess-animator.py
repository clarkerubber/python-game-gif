from tempfile import TemporaryFile

from chess.pgn import read_game
import chess.svg

from flask import Flask, send_file

import requests
import argparse
import cairosvg
import imageio

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


parser = argparse.ArgumentParser(description=__doc__)

parser.add_argument("--css", dest="css", type=argparse.FileType("r"), default="default.css")

settings = parser.parse_args()

app = Flask(__name__)

style = settings.css.read() if settings.css else None


@app.route('/<gameid>.gif', methods=['GET'])
def serve_gif(gameid):
    result = requests.get(f'https://lichess.org/game/export/{gameid}')

    game = read_game(StringIO(result.text))
    size = 360
    tempfile = TemporaryFile()

    with imageio.get_writer(tempfile, mode='I', format='gif', fps=1) as writer:
        node = game
        while not node.is_end():
            nextNode = node.variation(0)
            board_svg = chess.svg.board(node.board(), coordinates=False, flipped=False, size=size, style=style)
            board_png = imageio.imread(cairosvg.svg2png(bytestring=board_svg))
            writer.append_data(board_png)
            node = nextNode

    tempfile.seek(0)

    return send_file(tempfile, mimetype='image/gif')


if __name__ == '__main__':
    app.run(host='0.0.0.0')