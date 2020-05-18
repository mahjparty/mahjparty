from flask import Flask
from flask import request
from maj import Game
import json
import string
import random
import datetime
import re

app = Flask(__name__)

games = {}

def rand_id():
  letters = string.ascii_lowercase + string.digits + string.ascii_uppercase
  return ''.join([random.choice(letters) for i in range(10)])

@app.route('/')
def hello_world():
  return 'Hello, World!'

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
  game = games.get(game_id)
  if game is None:
    return err("Invalid game id")

  res = game.add_player(player_id, player_name)
  if res is not None:
    return err(res)

  return send({"success": True})

@app.route('/create_game')
def create_game():
  game_id = rand_id()
  start_time = datetime.datetime.now()
  game = Game(start_time)
  games[game_id] = game
  return send({"game_id": game_id})

@app.route('/game_state')
def get_game_state():
  game_id = request.args.get('game_id')
  player_id = request.args.get('player_id')
  if game_id is None or player_id is None:
    return err("Missing game_id/player_id")
  game = games.get(game_id)
  if game is None:
    return err("Invalid game id")
  else:
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

  tiles = parse_tiles(request.args.get('tiles'))
  if tiles is None:
    return err("Invalid tiles")

  res = game.end_call_phase(player_id, tiles)
  if res is None:
    return send(game.get_state(player_id))
  else:
    return err(res)
