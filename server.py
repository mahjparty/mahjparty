from flask import Flask
from flask import request
from maj import Game
import json
import string
import random
import datetime
import re
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

games = {}

def rand_id():
  letters = string.ascii_lowercase + string.digits + string.ascii_uppercase
  return ''.join([random.choice(letters) for i in range(16)])

@app.route('/')
def hello_world():
  return 'Welcome to the Maj API!'

def send(jsn):
  return json.dumps(jsn)

def err(msg):
  return send({"error": msg})

def clean(text):
  return re.sub(r'[^A-Za-z0-9_ \.-]+', "", text)

def get_game_player():
  game_id = request.args.get('game_id')
  player_id = request.args.get('player_id')
  if game_id is None or player_id is None:
    return None, "Missing game_id/player_id"
  game = games.get(game_id)
  if game is None:
    return None, "Invalid game id"

  if not game.valid_player(player_id):
    return None, "Invalid player id"

  return game, player_id

def parse_tiles(tiles):
  if tiles is None:
    return None

  if tiles == "":
    return []

  try:
    return [int(t) for t in tiles.split(',')]
  except ValueError:
    return None

def parse_int(num):
  if num is None:
    return None

  try:
    return int(num)
  except ValueError:
    return None

def parse_bool(s):
  if s is None:
    return None

  if s.lower() == "true":
    return True
  elif s.lower() == "false":
    return False
  else:
    return None

@app.route('/add_player')
def add_player():
  game_id = request.args.get('game_id')
  player_id = request.args.get('player_id')
  player_name = request.args.get('player_name')
  if game_id is None or player_id is None:
    return err("Missing game_id/player_id")
  player_id = clean(player_id)
  player_name = clean(player_name or "")[:20]
  game = games.get(game_id)
  if game is None:
    return err("Invalid game id")

  res = game.add_player(player_id, player_name)
  if res is not None:
    return err(res)

  return send(game.get_state(player_id))

@app.route('/create_game')
def create_game():
  game_id = rand_id()
  start_time = datetime.datetime.now()
  game = Game(start_time)
  games[game_id] = game
  return send({"game_id": game_id})

@app.route('/game_state')
def get_game_state():
  game, player_id = get_game_player()
  if game is None:
    return err(player_id)

  return send(game.get_state(player_id))

@app.route('/offer_tiles')
def offer_tiles():
  game, player_id = get_game_player()
  if game is None:
    return err(player_id)

  tiles = parse_tiles(request.args.get('tiles'))
  if tiles is None:
    return err("Invalid tiles")

  res = game.offer_tiles(player_id, tiles)
  if res is None:
    return send(game.get_state(player_id))
  else:
    return err(res)

@app.route('/commit_offered')
def commit_offered():
  game, player_id = get_game_player()
  if game is None:
    return err(player_id)

  res = game.commit_offered(player_id)
  if res is None:
    return send(game.get_state(player_id))
  else:
    return err(res)

@app.route('/rearrange_tiles')
def rearrange_tiles():
  game, player_id = get_game_player()
  if game is None:
    return err(player_id)

  tiles = parse_tiles(request.args.get('tiles'))
  if tiles is None:
    return err("Invalid tiles")

  res = game.rearrange_tiles(player_id, tiles)
  if res is None:
    return send(game.get_state(player_id))
  else:
    return err(res)

@app.route('/suggest_trade')
def suggest_trade():
  game, player_id = get_game_player()
  if game is None:
    return err(player_id)

  num_offered = parse_int(request.args.get('num_offered'))
  if num_offered is None:
    return err("Invalid offer")

  res = game.suggest_trade(player_id, num_offered)
  if res is None:
    return send(game.get_state(player_id))
  else:
    return err(res)

@app.route('/discard_tile')
def discard_tile():
  game, player_id = get_game_player()
  if game is None:
    return err(player_id)

  tile = parse_tiles(request.args.get('tile'))
  if tile is None or len(tile) != 1:
    return err("Invalid tiles")

  res = game.discard_tile(player_id, tile[0])
  if res is None:
    return send(game.get_state(player_id))
  else:
    return err(res)

@app.route('/draw_tile')
def draw_tile():
  game, player_id = get_game_player()
  if game is None:
    return err(player_id)

  res = game.draw_tile(player_id)
  if res is None:
    return send(game.get_state(player_id))
  else:
    return err(res)

@app.route('/call_tile')
def call_tile():
  game, player_id = get_game_player()
  if game is None:
    return err(player_id)

  maj = parse_bool(request.args.get('maj'))
  if maj is None:
    return err("Invalid maj state")

  res = game.call_tile(player_id, maj)
  if res is None:
    return send(game.get_state(player_id))
  else:
    return err(res)

@app.route('/waive_call')
def waive_call():
  game, player_id = get_game_player()
  if game is None:
    return err(player_id)

  res = game.waive_call(player_id)
  if res is None:
    return send(game.get_state(player_id))
  else:
    return err(res)

@app.route('/end_call_phase')
def end_call_phase():
  game, player_id = get_game_player()
  if game is None:
    return err(player_id)

  res = game.end_call_phase(player_id)
  if res is None:
    return send(game.get_state(player_id))
  else:
    return err(res)

@app.route('/place_hold')
def place_hold():
  game, player_id = get_game_player()
  if game is None:
    return err(player_id)

  maj = parse_bool(request.args.get('maj'))
  if maj is None:
    return err("Invalid maj state")

  res = game.place_hold(player_id, maj)
  if res is None:
    return send(game.get_state(player_id))
  else:
    return err(res)

@app.route('/show_tiles')
def show_tiles():
  game, player_id = get_game_player()
  if game is None:
    return err(player_id)

  tiles = parse_tiles(request.args.get('tiles'))
  if tiles is None:
    return err("Invalid tiles")

  res = game.show_tiles(player_id, tiles)
  if res is None:
    return send(game.get_state(player_id))
  else:
    return err(res)

@app.route('/claim_maj')
def claim_maj():
  game, player_id = get_game_player()
  if game is None:
    return err(player_id)

  res = game.claim_maj(player_id)
  if res is None:
    return send(game.get_state(player_id))
  else:
    return err(res)

@app.route('/retract_maj')
def retract_maj():
  game, player_id = get_game_player()
  if game is None:
    return err(player_id)

  res = game.retract_maj(player_id)
  if res is None:
    return send(game.get_state(player_id))
  else:
    return err(res)

@app.route('/restart_game')
def restart_game():
  game, player_id = get_game_player()
  if game is None:
    return err(player_id)

  res = game.restart_game(player_id)
  if res is None:
    return send(game.get_state(player_id))
  else:
    return err(res)

@app.route('/swap_joker')
def swap_joker():
  game, player_id = get_game_player()
  if game is None:
    return err(player_id)

  tile = parse_tiles(request.args.get('tile'))
  if tile is None or len(tile) != 1:
    return err("Invalid tiles")

  joker = parse_tiles(request.args.get('joker'))
  if joker is None or len(joker) != 1:
    return err("Invalid jokers")

  res = game.swap_joker(player_id, tile[0], joker[0])
  if res is None:
    return send(game.get_state(player_id))
  else:
    return err(res)

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, processes=1)
