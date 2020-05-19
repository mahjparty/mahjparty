from enum import Enum
import datetime
import random

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
    self.maj = False

  def take_tile(self, tile):
    self.hand.append(tile)

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
    self.hand, group = self.pick_tiles(self.hand, tiles)
    self.board.append(group)

  def claim_maj(self):
    self.maj = True

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
    return str(self) #TODO

class GamePhase(Enum):
  WAITING_PLAYERS = 1
  TRADING_MANDATORY = 2
  TRADING_OPTIONAL_SUGGEST = 3
  TRADING_OPTIONAL_EXECUTE = 4
  DISCARD = 5
  START_TURN = 6
  PENDING_CALL = 7
  WINNER = 8

def create_deck():
  deck = []
  idx = 0
  for j in range(4):
    for i in range(1,9):
      deck.append(Tile(TileTypes.DOT, i, idx))
      deck.append(Tile(TileTypes.BAMBOO, i, idx+1))
      deck.append(Tile(TileTypes.CRACK, i, idx+2))
      idx += 3

    for i in range(1,4):
      deck.append(Tile(TileTypes.WIND, i, idx))
      idx += 1

    for i in range(1,3):
      deck.append(Tile(TileTypes.DRAGON, i, idx))
      idx += 1

  for i in range(1,8):
    deck.append(Tile(TileTypes.FLOWER, i, idx))
    idx += 1

  for j in range(1,8):
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
    self.draw_wait_duration = 1
    self.call_wait_duration = 2
    self.start_ts = None
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
      "top_discard": str(self.top_discard),
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
      "timeout_elapsed": self.timeout_elapsed()
    }

  def show_log(self):
    return [
      ((ts - datetime.datetime(1970, 1, 1)).total_seconds(), msg) for
      ts, msg in self.log_entries[-10:]
    ]

  def log(self, msg):
    self.log_entries.append((datetime.datetime.now(), msg))

  def validate_name(self, player_name):
    names = (p.name for p in self.players.values())
    while player_name is None or player_name in names:
      player_name = rand_player_name()

    return player_name

  def add_player(self, player_id, player_name):
    player_name = self.validate_name(player_name)

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
        self.phase != GamePhase.TRADING_OPTIONAL_EXECUTE):
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
    return player_idx == ((self.next_player-1) % len(self.player_seq))

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
    self.next_player = (self.next_player+1) % len(self.player_seq)
    self.waived = set()
    self.call_idx = None
    self.maj = False
    self.start_ts = datetime.datetime.now()
    return None

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
    self.log("{} drew a tile.".format(player.name))

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

    self.phase = GamePhase.PENDING_CALL
    self.start_ts = datetime.datetime.now()

    player_idx = self.find_player_idx(player_id)
    if self.call_idx is None or self.has_call_priority(player_idx, is_maj, self.call_idx, self.maj):
      if self.call_idx is not None:
        # Can't call again if you already lost priority
        self.waived.add(self.player_seq[self.call_idx])
      self.call_idx = player_idx
      player = self.players[player_id]
      if is_maj:
        self.log("{} called the tile with maj.".format(player.name))
      else:
        self.log("{} called the tile.".format(player.name))
    else:
      return "Another player with higher priority has already called"

    return None

  def can_call(self, idx, is_maj):
    pid = self.player_seq[idx]
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

  def timeout_elapsed(self):
    now = datetime.datetime.now()
    if self.phase == GamePhase.START_TURN:
      return (now - self.start_ts).total_seconds() >= self.draw_wait_duration
    elif self.phase == GamePhase.PENDING_CALL:
      return (now - self.start_ts).total_seconds() >= self.call_wait_duration
    else:
      return None # n/a

  def waive_call(self, player_id):
    self.waived.add(player_id)
    return None

  def end_call_phase(self, player_id, tiles):
    if self.phase != GamePhase.PENDING_CALL:
      return "Wrong game phase to show tiles"

    player_idx = self.find_player_idx(player_id)
    if self.call_idx != player_idx:
      return "A different player has priority on this call, or you did not call yet"

    if not self.all_waived() and not self.timeout_elapsed():
      return "Let other players have a chance to call first"

    player = self.players[player_id]

    self.log("The {} went to {}.".format(self.top_discard.nice_name(), player.name))
    player.take_tile(self.top_discard)
    player.show_tiles(tiles + [self.top_discard])
    self.top_discard = None

    if self.maj:
      self.phase = GamePhase.WINNER
      player.claim_maj()
      self.log("{} claims maj.".format(player.name))
    else:
      self.phase = GamePhase.DISCARD
      self.next_player = player_idx

