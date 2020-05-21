from enum import Enum
import datetime
import random
import json

with open("www/tile_data.json") as f:
  tile_data = json.load(f)

def rand_player_name():
  part1 = ["Happy", "Proud", "Excited", "Curious", "Quick", "Honest",
           "Cheery", "Ambitious", "Trustworthy", "Energetic", "Hungry",
           "Speedy", "Hearty"]
  part2 = ["Mouse", "Lamb", "Kitten", "Puppy", "Snake", "Piglet",
           "Pony", "Frog", "Ostrich", "Elephant", "Elk"]
  return random.choice(part1) + " " + random.choice(part2)

def jsonTiles(tiles):
  return [str(t) for t in tiles]

class Player:
  def __init__(self, name):
    self.name = name
    self.hand = []
    self.offered = []
    self.num_offered = None
    self.board = []
    self.disqualified = False

  def take_tile(self, tile):
    self.hand.append(tile)

  def take_tile_offered(self, tile):
    self.offered.append(tile)

  def take_tiles(self, tiles):
    self.hand += tiles

  # pick out one tile
  def pick_tile(self, tiles, choice):
    res1 = []
    res2 = None
    picked = False
    for tile in tiles:
      if tile.idx == choice and not picked:
        res2 = tile
        picked = True
      else:
        res1.append(tile)

    return res1, res2

  # split tiles into two groups: those kept, and those chosen
  def pick_tiles(self, tiles, choices):
    res = []
    for choice in choices:
      tiles, sel = self.pick_tile(tiles, choice)
      if sel is not None:
        res.append(sel)

    return tiles, res

  # merge two sets of tiles into one group (on the left)
  def merge_left(self, left, right):
    return left+right, []

  def offer_tiles(self, offer_tiles):
    if self.offered:
      self.hand, self.offered = self.merge_left(self.hand, self.offered)

    self.hand, self.offered = self.pick_tiles(self.hand, offer_tiles)

  def rearrange_tiles(self, tiles):
    new_hand = []
    for choice in tiles:
      self.hand, sel = self.pick_tile(self.hand, choice)
      if sel:
        new_hand.append(sel)
      self.offered, sel = self.pick_tile(self.offered, choice)
      if sel:
        new_hand.append(sel)

    self.hand, _ = self.merge_left(self.hand, new_hand)

  def send_offer(self, other):
    other.take_tiles(self.offered)
    self.offered = []

  def discard_tile(self, tile):
    self.hand, discarded = self.pick_tile(self.hand, tile)
    return discarded

  def show_tiles(self, tiles):
    if self.offered:
      self.hand, self.offered = self.merge_left(self.hand, self.offered)
    self.hand, group = self.pick_tiles(self.hand, tiles)
    self.board.append(group)

  def find_tile(self, tile):
    for t in self.hand:
      if t.idx == tile:
        return t

    return None

  def swap_tile(self, lose_tile, gain_tile):
    new_hand = []
    found = False
    for t in self.hand:
      if t.idx == lose_tile.idx:
        new_hand.append(gain_tile)
        found = True
      else:
        new_hand.append(t)
    self.hand = new_hand
    return found

  def swap_joker(self, other, swap_tile, joker):
    for group in self.board:
      for i in range(len(group)):
        if (group[i].idx == joker and
            group[i].typ == TileTypes.JOKER):
          if other.swap_tile(swap_tile, group[i]):
            group[i] = swap_tile
            return True

    return False

  def has_maj(self):
    return len(self.hand) == 0 and sum((len(g) for g in self.board)) == 14

  def json_hand(self):
    return jsonTiles(self.hand)

  def json_offered(self):
    return jsonTiles(self.offered)

  def json_board(self):
    return [jsonTiles(g) for g in self.board]

class TileTypes(Enum):
  DOT = 'O'
  BAMBOO = 'B'
  CRACK = 'C'
  WIND = 'W'
  DRAGON = 'D'
  FLOWER = 'F'
  JOKER = 'J'

class Tile:
  def __init__(self, typ, num, idx):
    self.typ = typ
    self.num = num
    self.idx = idx

  def __str__(self):
    return str(self.typ.value) + str(self.num) + ":" + str(self.idx)

  def __repr__(self):
    return str(self)

  def nice_name(self):
    data = tile_data[self.typ.value]
    typ = data["type"]
    if typ == "numerical":
      return str(self.num) + " " + data["desc"]
    elif typ == "named":
      return data["named"][self.num-1]
    elif typ == "equivalent":
      return data["desc"]
    else:
      return str(self)

class GamePhase(Enum):
  WAITING_PLAYERS = 1
  TRADING_MANDATORY = 2
  TRADING_OPTIONAL_SUGGEST = 3
  TRADING_OPTIONAL_EXECUTE = 4
  DISCARD = 5
  START_TURN = 6
  PENDING_CALL = 7
  PENDING_SHOW = 8
  SHOWING_MAJ = 9
  WINNER = 10
  WALL = 11

def create_deck():
  deck = []
  idx = 0
  for j in range(4):
    for i in range(1,10):
      deck.append(Tile(TileTypes.DOT, i, idx))
      deck.append(Tile(TileTypes.BAMBOO, i, idx+1))
      deck.append(Tile(TileTypes.CRACK, i, idx+2))
      idx += 3

    for i in range(1,5):
      deck.append(Tile(TileTypes.WIND, i, idx))
      idx += 1

    for i in range(1,4):
      deck.append(Tile(TileTypes.DRAGON, i, idx))
      idx += 1

  for i in range(1,9):
    deck.append(Tile(TileTypes.FLOWER, i, idx))
    idx += 1

  for j in range(1,9):
    deck.append(Tile(TileTypes.JOKER, 1, idx))
    idx += 1

  return deck

class Game:
  def __init__(self, start_time):
    self.init_ts = datetime.datetime.now()
    self.players = {}
    self.player_seq = []
    self.max_players = 4
    self.phase = GamePhase.WAITING_PLAYERS
    self.trades = 0
    self.deck = create_deck()
    self.next_player = 0
    self.discard_pile = []
    self.top_discard = None
    self.call_idx = None
    self.maj = False
    self.log_entries = []
    self.draw_wait_duration = 5
    self.call_wait_duration = 5
    self.start_ts = datetime.datetime.now()
    self.waived = set()
    random.shuffle(self.deck)

  def valid_player(self, player_id):
    return player_id in self.players

  def player_idx(self, idx):
    return self.players[self.player_seq[idx]]

  def find_player_idx(self, player_id):
    return self.player_seq.index(player_id)

  def get_state(self, pid):
    return {
      "deck": ','.join((str(x) for x in self.deck)),
      "deck_size": len(self.deck),
      "hand": self.players[pid].json_hand(),
      "phase": self.phase.name,
      "trades": self.trades,
      "player_names": [
          self.players[i].name for i in self.player_seq
      ],
      "boards": [
        self.players[i].json_board() for i in self.player_seq
      ],
      "num_offered": self.players[pid].num_offered,
      "offered": self.players[pid].json_offered(),
      "discard_pile": jsonTiles(self.discard_pile),
      "top_discard": self.top_discard and str(self.top_discard),
      "next_player": self.next_player,
      "your_turn": self.is_player_turn(pid),
      "player_idx": self.find_player_idx(pid),
      "call_idx": self.call_idx,
      "maj": self.maj,
      "log": self.show_log(),
      "call_wait_duration": self.call_wait_duration,
      "draw_wait_duration": self.draw_wait_duration,
      "all_waived": self.all_waived(),
      "can_call": [
        self.can_call(i, False) for i in range(len(self.player_seq))
      ],
      "can_call_maj": [
        self.can_call(i, True) for i in range(len(self.player_seq))
      ],
      "timeout_elapsed": self.timeout_elapsed(),
      "timeout_deadline": self.ts_to_epoch(self.timeout_deadline()),
      "disqualified": [
        self.players[i].disqualified for i in self.player_seq
      ],
    }

  def ts_to_epoch(self, ts):
    return ts.timestamp()

  def show_log(self):
    return [
      (self.ts_to_epoch(ts), msg) for
      ts, msg in self.log_entries[-10:]
    ]

  def log(self, msg):
    self.log_entries.append((datetime.datetime.now(), msg))

  def validate_name(self, player_id, player_name):
    names = (p.name for pid, p in self.players.items() if pid != player_id)
    while player_name is None or player_name in names:
      player_name = rand_player_name()

    return player_name

  def add_player(self, player_id, player_name):
    player_name = self.validate_name(player_id, player_name)

    if player_id in self.players:
      old_name = self.players[player_id].name
      if player_name and player_name != old_name:
        self.log("{} has renamed to {}.".format(old_name, player_name))
        self.players[player_id].name = player_name
      return None
    else:
      if len(self.players) >= self.max_players:
        return "Game is full"

      self.log("{} has joined the game.".format(player_name))
      self.players[player_id] = Player(player_name)
      self.player_seq.append(player_id)

    if len(self.players) >= self.max_players:
      self.start_trading_phase()

    return None

  def deal_tiles(self):
    # 13 tiles each, East gets an extra
    for i in range(13*4+1):
      pid = self.player_seq[i % 4]
      tile = self.deck.pop()
      self.players[pid].take_tile(tile)

    self.log("The initial hands have been dealt.")

  def start_trading_phase(self):
    random.shuffle(self.player_seq)
    self.deal_tiles()
    self.phase = GamePhase.TRADING_MANDATORY

  def offer_tiles(self, player_id, tiles):
    if (self.phase != GamePhase.TRADING_MANDATORY and
        self.phase != GamePhase.TRADING_OPTIONAL_EXECUTE and
        self.phase != GamePhase.PENDING_SHOW and
        self.phase != GamePhase.SHOWING_MAJ):
        return "Wrong game phase to offer tiles"

    self.players[player_id].offer_tiles(tiles)

    if self.phase == GamePhase.TRADING_MANDATORY:
      ready = all((len(p.offered) == 3 for p in self.players.values()))
      if ready:
        self.do_mandatory_trade()
    elif self.phase == GamePhase.TRADING_OPTIONAL_EXECUTE:
      ready = all((len(p.offered) == p.num_offered for p in self.players.values()))
      if ready:
        self.do_optional_trade()

    return None

  def suggest_trade(self, player_id, num_tiles):
    if self.phase == GamePhase.TRADING_OPTIONAL_SUGGEST:
      self.players[player_id].num_offered = num_tiles

      num_offered = [p.num_offered for p in self.players.values()]
      if all((n is not None for n in num_offered)):
        skip = True
        for idx in range(2):
          p1 = self.player_idx(idx)
          p2 = self.player_idx(idx+2)
          num = min(p1.num_offered, p2.num_offered)
          p1.num_offered = num
          p2.num_offered = num
          if num > 0:
            skip = False

          self.log("{} and {} agreed to trade {} tiles.".format(p1.name, p2.name, num))

        if skip:
          self.start_main()
        else:
          self.phase = GamePhase.TRADING_OPTIONAL_EXECUTE

      return None
    else:
      return "Wrong game phase to suggest a trade"

  def do_mandatory_trade(self):
    dirs = [1, 2, -1, -1, 2, 1]
    dirStrs = ["right", "across", "left", "left", "across", "right"];
    dir = dirs[self.trades]
    self.log("Players traded 3 tiles {}.".format(dirStrs[self.trades]))
    for idx in range(len(self.player_seq)):
      idx2 = (idx + dir) % len(self.player_seq)
      self.player_idx(idx).send_offer(self.player_idx(idx2))

    self.trades += 1
    if self.trades == 6:
      self.phase = GamePhase.TRADING_OPTIONAL_SUGGEST

  def do_optional_trade(self):
    for idx in range(2):
      p1 = self.player_idx(idx)
      p2 = self.player_idx(idx+2)

      self.log("{} and {} traded {} tiles.".format(p1.name, p2.name, p1.num_offered))

      p1.send_offer(p2)
      p2.send_offer(p1)

    self.start_main()

  def start_main(self):
    self.phase = GamePhase.DISCARD
    self.next_player = 0 # East

  def is_player_turn(self, pid):
    return pid == self.player_seq[self.next_player]

  def is_prev_turn(self, pid):
    player_idx = self.find_player_idx(pid)
    nxt = self.get_prev_player(self.next_player)
    return player_idx == nxt

  def discard_tile(self, player_id, tile):
    if self.phase != GamePhase.DISCARD:
      return "Wrong game phase to discard a tile"

    if not self.is_player_turn(player_id):
      return "Not your turn"

    player = self.players[player_id]
    discarded = player.discard_tile(tile)
    if discarded is None:
      return "Invalid tile"
    self.log("{} discarded {}.".format(player.name, discarded.nice_name()))

    self.top_discard = discarded
    self.phase = GamePhase.START_TURN
    nxt = self.get_next_player(self.next_player)
    if nxt is None:
      self.wall_game()
    else:
      self.next_player = nxt
    self.waived = set()
    self.call_idx = None
    self.maj = False
    self.start_ts = datetime.datetime.now()
    return None

  def get_prev_player(self, nxt):
    for i in range(len(self.player_seq)):
      nxt = (nxt-1) % len(self.player_seq)
      player = self.players[self.player_seq[nxt]]
      if not player.disqualified:
        return nxt

    return None

  def get_next_player(self, nxt):
    for i in range(len(self.player_seq)):
      nxt = (nxt+1) % len(self.player_seq)
      player = self.players[self.player_seq[nxt]]
      if not player.disqualified:
        return nxt

    return None

  def wall_game(self):
    self.phase = GamePhase.WALL
    self.log("All players disqualified. It's a wall game!")

  def rearrange_tiles(self, player_id, tiles):
    player = self.players[player_id]
    player.rearrange_tiles(tiles)
    return None

  def draw_tile(self, player_id):
    if self.phase != GamePhase.START_TURN:
      return "Wrong game phase to draw a tile"

    if not self.is_player_turn(player_id):
      return "Not your turn"

    if not self.all_waived() and not self.timeout_elapsed():
      return "Let other players have a chance to call first"

    player = self.players[player_id]

    if len(self.deck) == 0:
      self.log("No tiles left for {} to draw. It's a wall game!".format(player.name))
      self.phase = GamePhase.WALL
      return None

    tile = self.deck.pop()
    player.take_tile(tile)
    self.log("{} drew a tile ({} remaining).".format(player.name, len(self.deck)))

    if self.top_discard:
      self.discard_pile.append(self.top_discard)
    self.top_discard = None
    self.phase = GamePhase.DISCARD
    return None

  # return true if player 1 has call priority over player 2
  def has_call_priority(self, idx1, maj1, idx2, maj2):
    if maj1 and not maj2:
      return True
    if maj2 and not maj1:
      return False
    # check wrap-around
    if idx1 <= self.next_player:
      idx1 += len(self.player_seq)
    if idx2 <= self.next_player:
      idx2 += len(self.player_seq)

    return idx1 < idx2

  def call_tile(self, player_id, is_maj):
    if (self.phase != GamePhase.START_TURN and
        self.phase != GamePhase.PENDING_CALL):
      return "Wrong game phase to call a tile"

    if self.is_prev_turn(player_id):
      return "Cannot call your own discard"

    player = self.players[player_id]

    if player.disqualified:
      return "Disqualified"

    self.phase = GamePhase.PENDING_CALL
    # Optional: Reset timer:
    # self.start_ts = datetime.datetime.now()

    player_idx = self.find_player_idx(player_id)
    if self.call_idx is None or self.has_call_priority(player_idx, is_maj, self.call_idx, self.maj):
      if self.call_idx is not None:
        # Can't call again if you already lost priority
        self.waived.add(self.player_seq[self.call_idx])
      self.call_idx = player_idx
      self.maj = is_maj
      if is_maj:
        self.log("{} called the tile with maj.".format(player.name))
      else:
        self.log("{} called the tile.".format(player.name))
    else:
      return "Another player with higher priority has already called"

    return None

  def can_call(self, idx, is_maj):
    pid = self.player_seq[idx]
    if self.top_discard is None:
      return False
    if self.top_discard.typ == TileTypes.JOKER:
      return False
    if self.players[pid].disqualified:
      return False
    if self.is_prev_turn(pid):
      return False
    if pid in self.waived:
      return False
    if self.call_idx is None:
      return True
    if idx == self.call_idx:
      return False

    return self.has_call_priority(idx, is_maj, self.call_idx, self.maj)

  def all_waived(self):
    if (self.phase != GamePhase.START_TURN and
        self.phase != GamePhase.PENDING_CALL):
        return None #n/a

    for i in range(len(self.player_seq)):
      if self.can_call(i, True):
        return False

    return True

  def timeout_deadline(self):
    if self.phase == GamePhase.START_TURN:
      return self.start_ts + datetime.timedelta(seconds=self.draw_wait_duration)
    elif self.phase == GamePhase.PENDING_CALL:
      return self.start_ts + datetime.timedelta(seconds=self.call_wait_duration)
    else:
      return datetime.datetime(1970, 1, 1)

  def timeout_elapsed(self):
    now = datetime.datetime.now()
    deadline = self.timeout_deadline()
    return now >= deadline

  def waive_call(self, player_id):
    self.waived.add(player_id)
    return None

  def end_call_phase(self, player_id):
    if self.phase != GamePhase.PENDING_CALL:
      return "Cannot end call phase yet"

    if not self.all_waived() and not self.timeout_elapsed():
      return "Let other players have a chance to call first"

    player_idx = self.find_player_idx(player_id)
    if self.call_idx != player_idx:
      return "Not your turn to call"

    player = self.players[player_id]
    if player.disqualified:
      return "Disqualified"

    self.next_player = player_idx

    player.take_tile_offered(self.top_discard)
    self.log("The {} went to {}.".format(self.top_discard.nice_name(), player.name))
    self.top_discard = None

    if self.maj:
      self.phase = GamePhase.SHOWING_MAJ
      self.log("{} claims maj.".format(player.name))
    else:
      self.phase = GamePhase.PENDING_SHOW

  def show_tiles(self, player_id, tiles):
    if (self.phase != GamePhase.PENDING_SHOW and
        self.phase != GamePhase.SHOWING_MAJ):
      return "Wrong game phase to show tiles"

    player_idx = self.find_player_idx(player_id)
    if self.next_player != player_idx:
      return "Not your turn to call"

    if len(tiles) < 3 and self.phase == GamePhase.PENDING_SHOW:
      return "Must reveal at least three tiles."

    player = self.players[player_id]

    if player.disqualified:
      return "Disqualified"

    player.show_tiles(tiles)
    self.log("{} showed tiles.".format(player.name))

    if player.has_maj():
      self.phase = GamePhase.WINNER
    elif self.phase == GamePhase.PENDING_SHOW:
      self.phase = GamePhase.DISCARD
    elif self.phase == GamePhase.SHOWING_MAJ:
      self.phase = GamePhase.SHOWING_MAJ

  def claim_maj(self, player_id):
    if self.phase != GamePhase.DISCARD:
      return "Wrong game phase to claim maj"

    if not self.is_player_turn(player_id):
      return "Not your turn"

    player = self.players[player_id]
    if player.disqualified:
      return "Disqualified"

    self.phase = GamePhase.SHOWING_MAJ
    self.log("{} claims maj.".format(player.name))

  def retract_maj(self, player_id):
    if self.phase != GamePhase.WINNER:
      return "Wrong game phase to retract maj"

    if not self.is_player_turn(player_id):
      return "Not your turn"

    player = self.players[player_id]
    if player.disqualified:
      return "Disqualified"

    player.disqualified = True
    self.phase = GamePhase.START_TURN
    self.log("{} retracted maj.".format(player.name))
    nxt = self.get_next_player(self.next_player)
    if nxt is None:
      self.wall_game()
    else:
      self.next_player = nxt

  def swap_joker(self, player_id, tile, joker):
    if self.phase not in [GamePhase.DISCARD, GamePhase.START_TURN]:
      return "Wrong game phase to swap joker"

    if not self.is_player_turn(player_id):
      return "Not your turn"

    player = self.players[player_id]
    if player.disqualified:
      return "Disqualified"

    swap_tile = player.find_tile(tile)
    if swap_tile is None:
      return "You don't have that tile"

    for p in self.players.values():
      if p.swap_joker(player, swap_tile, joker):
        self.log("{} traded a {} for a joker.".format(
          player.name, swap_tile.nice_name()))
        return None

    return "Joker swap failed"

