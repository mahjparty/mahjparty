from enum import Enum
import datetime
import random
import json

with open("docs/tile_data.json") as f:
  tile_data = json.load(f)

with open("words.txt") as f:
  word_data = [w.strip() for w in f]

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
    self.restart_game()

  def restart_game(self):
    self.hand = []
    self.offered = []
    self.num_offered = None
    self.commit_offered = False
    self.board = []
    self.disqualified = False
    self.reveal_hand = False

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

  def send_offer(self, other, num_send, leftovers):
    if len(self.offered) == num_send:
      other.take_tiles(self.offered)
    elif len(self.offered) > num_send:
      extra = len(self.offered) - num_send
      other.take_tiles(self.offered[extra:])
      leftovers += self.offered[:extra]
    elif len(self.offered) < num_send:
      missing = num_send - len(self.offered)
      other.take_tiles(self.offered + leftovers[:missing])
      leftovers = leftovers[missing:]

    self.offered = []
    return leftovers

  def discard_tile(self, tile):
    self.hand, discarded = self.pick_tile(self.hand, tile)
    return discarded

  def check_show_tiles(self, tiles, call_tile):
    ftiles = self.find_tiles(tiles)
    if len(ftiles) != len(tiles):
      return False
    if (not all((t.matches(call_tile) for t in ftiles))):
      return False

    return True

  def show_tiles(self, tiles):
    if self.offered:
      self.hand, self.offered = self.merge_left(self.hand, self.offered)
    self.hand, group = self.pick_tiles(self.hand, tiles)
    self.board.append(group)

  def find_tiles(self, tiles):
    res = []
    for t in tiles:
      ft = self.find_tile(t)
      if ft is not None:
        res.append(ft)
    return res

  def find_tile(self, tile):
    for t in (self.hand + self.offered):
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
      if not all((t.matches(swap_tile) for t in group)):
        continue
      for i in range(len(group)):
        if (group[i].idx == joker and
            group[i].typ == TileTypes.JOKER):
          if other.swap_tile(swap_tile, group[i]):
            group[i] = swap_tile
            return True

    return False

  def can_call(self, tile):
    matches = sum((t.matches(tile) for t in self.hand))
    return matches >= 2

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

  def matches(self, other):
    # can't call a joker
    if other.typ == TileTypes.JOKER:
      return False

    # but you can always use a Joker to call
    if self.typ == TileTypes.JOKER:
      return True

    data = tile_data[other.typ.value]
    typ = data["type"]
    if typ == "numerical" or typ == "named":
      return self.typ == other.typ and self.num == other.num
    elif typ == "equivalent":
      return self.typ == other.typ
    else:
      return True # should be unreachable

class GamePhase(Enum):
  WAITING_PLAYERS = 1
  TRADING_MANDATORY = 2
  TRADING_OPTIONAL_SUGGEST = 3
  TRADING_OPTIONAL_EXECUTE = 4
  DISCARD = 5
  START_TURN = 6
  PENDING_SHOW = 8
  SHOWING_MAJ = 9
  WINNER = 10
  WALL = 11

class WaiveState(Enum):
  WAIVED = 1
  HOLD = 2
  HOLD_MAJ = 3
  CALL = 4
  CALL_MAJ = 5
  NONE = 6

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
  def __init__(self):
    self.players = {}
    self.player_seq = []
    self.max_players = 4
    self.phase = GamePhase.WAITING_PLAYERS
    self.log_entries = []
    self.restart_game(None)
    self.words = random.sample(word_data, 4)

  def restart_game(self, player_id):
    self.init_ts = datetime.datetime.now()
    self.trades = 0
    self.deck = create_deck()
    self.next_player = 0
    self.discard_pile = []
    self.top_discard = None
    self.call_idx = None
    self.maj = False
    self.draw_wait_duration = 5
    self.start_ts = datetime.datetime.now()
    self.called_tile = None
    self.waive_state = dict()
    random.shuffle(self.deck)

    if player_id:
      player = self.players[player_id]
      self.log("{} started a new game.".format(player.name))
      for p in self.players.values():
        p.restart_game()
      self.start_trading_phase()

  def words_key(self):
    return "".join([word[:3] for word in self.words])

  def words_full(self):
    return " ".join(self.words)

  def valid_player(self, player_id):
    return player_id in self.players

  def player_idx(self, idx):
    return self.players[self.player_seq[idx]]

  def find_player_idx(self, player_id):
    return self.player_seq.index(player_id)

  def get_state(self, pid):
    call_idx, maj = self.call_winner()
    return {
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
      "revealed_hands": [
        (self.players[i].json_hand() if
         (self.players[i].reveal_hand and self.phase in (GamePhase.WINNER, GamePhase.WALL))
         else None)
        for i in self.player_seq
      ],
      "commit_offered": self.players[pid].commit_offered,
      "num_offered": self.players[pid].num_offered,
      "offered": self.players[pid].json_offered(),
      "discard_pile": jsonTiles(self.discard_pile),
      "top_discard": self.top_discard and str(self.top_discard),
      "called_tile": self.called_tile and str(self.called_tile),
      "next_player": self.next_player,
      "your_turn": self.is_player_turn(pid),
      "player_idx": self.find_player_idx(pid),
      "log": self.show_log(),
      "draw_wait_duration": self.draw_wait_duration,
      "check_show_tiles": self.check_show_tiles(pid,
        [t.idx for t in self.players[pid].offered]),
      "your_waive_state": self.waive_state.get(pid, WaiveState.NONE).name,
      "waive_state": [
        self.waive_state.get(i, WaiveState.NONE).name for i in self.player_seq
      ],
      "can_call": [
        (self.can_call(i, False) is None) for i in range(len(self.player_seq))
      ],
      "can_call_maj": [
        (self.can_call(i, True) is None) for i in range(len(self.player_seq))
      ],
      "can_hold": [
        (self.can_hold(i, False) is None) for i in range(len(self.player_seq))
      ],
      "can_hold_maj": [
        (self.can_hold(i, True) is None) for i in range(len(self.player_seq))
      ],
      "can_end_call_phase": self.can_end_call_phase(),
      "call_idx": call_idx,
      "timeout_elapsed": self.timeout_elapsed(),
      "timeout_deadline": self.ts_to_epoch(self.timeout_deadline()),
      "disqualified": [
        self.players[i].disqualified for i in self.player_seq
      ],
      "words_full": self.words_full(),
      "blind_pass_allowed": self.blind_pass_allowed()
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
    while (player_name is None or
           len(player_name.strip()) == 0 or
           player_name in names):
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
        return "Sorry, this game is already full."

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
    return None

  def commit_offered(self, player_id):
    if (self.phase != GamePhase.TRADING_MANDATORY and
        self.phase != GamePhase.TRADING_OPTIONAL_EXECUTE):
        return "Wrong game phase to trade tiles"

    player = self.players[player_id]
    if self.phase == GamePhase.TRADING_MANDATORY:
      if not (len(player.offered) == 3 or self.blind_pass_allowed()):
        return "Need to trade three tiles"
    elif self.phase == GamePhase.TRADING_OPTIONAL_EXECUTE:
      if len(player.offered) != player.num_offered:
        return "Need to trade {} tiles".format(player.num_offered)

    for t in player.offered:
        if t.typ == TileTypes.JOKER:
            return "Jokers cannot be passed"

    player.commit_offered = True
    self.check_trade()
    return None

  def check_trade(self):
    if self.phase == GamePhase.TRADING_MANDATORY:
      ready = all(((len(p.offered) == 3 or self.blind_pass_allowed()) and p.commit_offered
                   for p in self.players.values()))
      if ready:
        self.do_mandatory_trade()
    elif self.phase == GamePhase.TRADING_OPTIONAL_EXECUTE:
      ready = all((len(p.offered) == p.num_offered and
                  (p.commit_offered or p.num_offered == 0)
                   for p in self.players.values()))
      if ready:
        self.do_optional_trade()

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

          self.log("{} and {} agreed to pass {} tiles.".format(p1.name, p2.name, num))

        if skip:
          self.start_main()
        else:
          self.phase = GamePhase.TRADING_OPTIONAL_EXECUTE

      return None
    else:
      return "Wrong game phase to suggest a trade"

  def blind_pass_allowed(self):
    return self.trades == 2 or self.trades == 5

  def do_mandatory_trade(self):
    dirs = [1, 2, -1, -1, 2, 1]
    dirStrs = ["right", "across", "left", "left", "across", "right"];
    dirNum = dirs[self.trades]
    self.log("Players passed 3 tiles {}.".format(dirStrs[self.trades]))

    nplayers = len(self.player_seq)

    if dirNum == 2:
      for offset in range(nplayers):
        idx1 = offset % nplayers
        idx2 = (offset + dirNum) % nplayers
        p1 = self.player_idx(idx1)
        p2 = self.player_idx(idx2)
        p1.send_offer(p2, 3, [])
        p1.commit_offered = False
    else:
      ocount = [len(self.player_idx(idx).offered) for idx in range(nplayers)]
      max_idx = None
      max_val = 0
      for idx in range(nplayers):
        val = ocount[idx]
        if val >= max_val:
          max_val = val
          max_idx = idx

      leftovers = []
      rng = range(nplayers)
      if dirNum == -1:
        rng = (-x for x in rng)
      for offset in rng:
        idx1 = (max_idx + offset) % nplayers
        idx2 = (max_idx + offset + dirNum) % nplayers
        p1 = self.player_idx(idx1)
        p2 = self.player_idx(idx2)
        leftovers = p1.send_offer(p2, ocount[idx2], leftovers)
        p1.commit_offered = False

      if len(leftovers) != 0:
        print("Leftovers remaining!")

    self.trades += 1
    if self.trades == 6:
      self.phase = GamePhase.TRADING_OPTIONAL_SUGGEST

  def do_optional_trade(self):
    for idx in range(2):
      p1 = self.player_idx(idx)
      p2 = self.player_idx(idx+2)
      p1.commit_offered = False
      p2.commit_offered = False

      self.log("{} and {} passed {} tiles.".format(p1.name, p2.name, p1.num_offered))

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
    self.waive_state = dict()
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

    res = self.can_end_call_phase()
    if res is not None:
      return res

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
    if idx1 < self.next_player:
      idx1 += len(self.player_seq)
    if idx2 < self.next_player:
      idx2 += len(self.player_seq)

    return idx1 <= idx2

  def place_hold(self, player_id, is_maj):
    if self.phase != GamePhase.START_TURN:
      return "Wrong game phase to call a tile"

    player = self.players[player_id]
    if player.disqualified:
      return "Disqualified"

    player_idx = self.find_player_idx(player_id)
    res = self.can_hold(player_idx, is_maj)
    if res is not None:
      return res

    if is_maj:
      self.waive_state[player_id] = WaiveState.HOLD_MAJ
    else:
      self.waive_state[player_id] = WaiveState.HOLD

    self.log("{} is deciding whether to call.".format(player.name))
    return None

  def call_tile(self, player_id, is_maj):
    if self.phase != GamePhase.START_TURN:
      return "Wrong game phase to call a tile"

    if self.is_prev_turn(player_id):
      return "Cannot call your own discard"

    player = self.players[player_id]

    if player.disqualified:
      return "Disqualified"

    player_idx = self.find_player_idx(player_id)
    res = self.can_call(player_idx, is_maj)
    if res is None:
      if self.call_idx is not None:
        # Can't call again if you already lost priority
        self.waive_state[self.player_seq[self.call_idx]] = WaiveState.WAIVED
      if is_maj:
        self.waive_state[player_id] = WaiveState.CALL_MAJ
      else:
        self.waive_state[player_id] = WaiveState.CALL
      if is_maj:
        self.log("{} called the tile with mahj.".format(player.name))
      else:
        self.log("{} called the tile.".format(player.name))
    else:
      return res

    return None

  def can_hold(self, idx, is_maj):
    player_id = self.player_seq[idx]
    if self.top_discard is None:
      return "No tile to call"
    if self.top_discard.typ == TileTypes.JOKER:
      return "Can't call a joker"
    if self.players[player_id].disqualified:
      return "Disqualified"
    if self.is_prev_turn(player_id):
      return "Can't call your own discard"
    if not is_maj and not self.players[player_id].can_call(self.top_discard):
      return "You don't have the right tiles to call"

    for i, pid in enumerate(self.player_seq):
      ws = self.waive_state.get(pid)
      if ws == WaiveState.CALL and not self.has_call_priority(idx, is_maj, i, False):
        return "You don't have call priority"
      if ws == WaiveState.CALL_MAJ and not self.has_call_priority(idx, is_maj, i, True):
        return "You don't have call priority"

    return None

  def can_call(self, idx, is_maj):
    res = self.can_hold(idx, is_maj)
    if res is not None:
      return res

    pid = self.player_seq[idx]
    ws = self.waive_state.get(pid)

    # these two tecnically aren't needed, but
    # they make the error message better
    if ws == WaiveState.WAIVED:
      return "You already decided not to call"
    if ws == WaiveState.CALL or ws == WaiveState.CALL_MAJ:
      return "You already called"

    if is_maj and ws != WaiveState.HOLD_MAJ:
      return "No mahj hold placed"
    if not is_maj and ws != WaiveState.HOLD:
      return "No hold placed"

    return None

  # returns call_idx, is_maj
  def call_winner(self):
    call_idx = None
    maj = None
    for idx, pid in enumerate(self.player_seq):
      ws = self.waive_state.get(pid)
      if ws == WaiveState.CALL:
        if call_idx is None or self.has_call_priority(idx, False, call_idx, maj):
          call_idx = idx
          maj = False
      elif ws == WaiveState.CALL_MAJ:
        if call_idx is None or self.has_call_priority(idx, True, call_idx, maj):
          call_idx = idx
          maj = True

    return call_idx, maj

  def can_end_call_phase(self):
    if self.phase != GamePhase.START_TURN:
        return "Wrong phase to call."

    holds = []
    for i, pid in enumerate(self.player_seq):
      if ((self.can_call(i, False) is None) or
          (self.can_call(i, True) is None)):
        holds.append(self.players[pid].name)

    if len(holds) == 1:
      return "{} is deciding whether to call.".format(holds[0])
    elif len(holds) > 1:
      return "{} players are deciding whether to call.".format(len(holds))

    if not self.timeout_elapsed():
      for idx, pid in enumerate(self.player_seq):
        ws = self.waive_state.get(pid, WaiveState.NONE)
        if ws == WaiveState.NONE and (self.can_hold(i, True) is None):
          return "Waiting for calls"

    return None

  def timeout_deadline(self):
    if self.phase == GamePhase.START_TURN:
      return self.start_ts + datetime.timedelta(seconds=self.draw_wait_duration)
    else:
      return datetime.datetime(1970, 1, 1)

  def timeout_elapsed(self):
    now = datetime.datetime.now()
    deadline = self.timeout_deadline()
    return now >= deadline

  def waive_call(self, player_id):
    player = self.players[player_id]
    ws = self.waive_state.get(player_id, WaiveState.NONE)
    if ws == WaiveState.CALL or ws == WaiveState.CALL_MAJ:
      return "You already called"
    elif ws == WaiveState.HOLD or ws == WaiveState.HOLD_MAJ:
      self.log("{} decided not to call.".format(player.name))

    self.waive_state[player_id] = WaiveState.WAIVED
    return None

  def end_call_phase(self, player_id):
    if self.phase != GamePhase.START_TURN:
      return "Cannot end call phase yet"

    player = self.players[player_id]
    if player.disqualified:
      return "Disqualified"

    res = self.can_end_call_phase()
    if res is not None:
      return res

    player_idx = self.find_player_idx(player_id)

    call_idx, maj = self.call_winner()
    if call_idx != player_idx:
      return "You do not have call priority"

    self.next_player = player_idx

    self.waive_state = dict()

    self.called_tile = self.top_discard
    player.take_tile_offered(self.top_discard)
    self.log("The {} went to {}.".format(self.top_discard.nice_name(), player.name))
    self.top_discard = None

    if maj:
      self.phase = GamePhase.SHOWING_MAJ
      self.log("{} claims mahj.".format(player.name))
    else:
      self.phase = GamePhase.PENDING_SHOW

  def check_show_tiles(self, player_id, tiles):
    if (self.phase != GamePhase.PENDING_SHOW and
        self.phase != GamePhase.SHOWING_MAJ):
      return "Wrong game phase to show tiles"

    player_idx = self.find_player_idx(player_id)
    if self.next_player != player_idx:
      return "Not your turn to call"

    if len(tiles) < 3 and self.phase == GamePhase.PENDING_SHOW:
      return "Must reveal at least three tiles"

    if len(tiles) < 1 or len(tiles) > 6:
      return "Must reveal 1-6 tiles at a time"

    player = self.players[player_id]

    if player.disqualified:
      return "Disqualified"

    if self.phase == GamePhase.PENDING_SHOW:
      if self.called_tile is None:
        return "Nothing to call"

      if not player.check_show_tiles(tiles, self.called_tile):
        return "Those tiles don't match {}!".format(self.called_tile.nice_name())

    return None

  def show_tiles(self, player_id, tiles):
    res = self.check_show_tiles(player_id, tiles)
    if res is not None:
      return res

    player = self.players[player_id]
    player.show_tiles(tiles)

    self.log("{} showed tiles.".format(player.name))

    self.called_tile = None

    if player.has_maj():
      self.phase = GamePhase.WINNER
    elif self.phase == GamePhase.PENDING_SHOW:
      self.phase = GamePhase.DISCARD
    elif self.phase == GamePhase.SHOWING_MAJ:
      self.phase = GamePhase.SHOWING_MAJ

  def claim_maj(self, player_id):
    if self.phase != GamePhase.DISCARD:
      return "Wrong game phase to claim mahj"

    if not self.is_player_turn(player_id):
      return "Not your turn"

    player = self.players[player_id]
    if player.disqualified:
      return "Disqualified"

    self.phase = GamePhase.SHOWING_MAJ
    self.log("{} claims mahj.".format(player.name))

  def retract_maj(self, player_id):
    if self.phase != GamePhase.WINNER:
      return "Wrong game phase to retract mahj"

    if not self.is_player_turn(player_id):
      return "Not your turn"

    player = self.players[player_id]
    if player.disqualified:
      return "Disqualified"

    player.disqualified = True
    self.phase = GamePhase.START_TURN
    self.log("{} retracted mahj.".format(player.name))
    nxt = self.get_next_player(self.next_player)
    if nxt is None:
      self.wall_game()
    else:
      self.next_player = nxt

  def reveal_hand(self, player_id):
    if (self.phase != GamePhase.WINNER and
        self.phase != GamePhase.WALL):
      return "Wrong game phase to reveal hand"

    player = self.players[player_id]
    player.reveal_hand = True
    self.log("{} revealed hand.".format(player.name))

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
        self.log("{} traded {} for a Joker.".format(
          player.name, swap_tile.nice_name()))
        return None

    return "Not a valid Joker swap"
