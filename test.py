import requests
import json
import random
import time

host = "http://localhost:5000"
p1="121"
p2="122"
p3="123"
p4="124"

def query(endpoint, showQuery=True, showRes=False, **kwargs):
  args = "&".join(["{}={}".format(x,y) for x, y in kwargs.items()])
  url = "{}/{}?{}".format(host, endpoint, args)
  if showQuery:
    print(url)
  c = requests.get(url)
  res = c.json()
  if showRes or "error" in res:
    print(json.dumps(res))
  return res

def sendTiles(tiles):
  return ",".join(t.split(":")[1] for t in tiles)

def randomOffer(pids, num=3):
  for pid in pids:
    gs = query("game_state", game_id=game_id, player_id=pid)

    while True:
      tiles = random.sample(gs["hand"], num)
      if not any((t.startswith("J") for t in tiles)):
        break

    query("offer_tiles", game_id=game_id, player_id=pid, tiles=sendTiles(tiles))
    query("commit_offered", game_id=game_id, player_id=pid)

def randomTiles(pid, num=3):
  gs = query("game_state", game_id=game_id, player_id=pid)
  return random.sample(gs["hand"], num)

def randomDiscard(pid):
  gs = query("game_state", game_id=game_id, player_id=pid)
  tiles = random.sample(gs["hand"], 1)
  query("discard_tile", game_id=game_id, player_id=pid, tile=sendTiles(tiles))

def draw(pid):
  query("draw_tile", game_id=game_id, player_id=pid)

def showState(pid=p3):
  return query("game_state", game_id=game_id, player_id=pid, showRes=True)

def get_active():
  for p in pids:
    s = showState(p)
    if s["your_turn"]:
      return p

def main():
  global game_id
  pids = [p1,p2,p3,p4]
  game = query("create_game")
  game_id = game["game_id"]
  query("add_player", game_id=game_id, player_id=p1, player_name="p1")
  query("add_player", game_id=game_id, player_id=p2, player_name="p2")
  query("add_player", game_id=game_id, player_id=p3)
  query("game_state", game_id=game_id, player_id=p3)
  query("add_player", game_id=game_id, player_id=p4, player_name="p4")

  for i in range(6):
    randomOffer(pids)
    showState()

  query("suggest_trade", game_id=game_id, player_id=p1, num_offered=2)
  query("suggest_trade", game_id=game_id, player_id=p2, num_offered=1)
  query("suggest_trade", game_id=game_id, player_id=p3, num_offered=3)
  query("suggest_trade", game_id=game_id, player_id=p4, num_offered=0)
  for p in pids:
    s = showState(p)
    num = s["num_offered"]
    if num > 0:
      randomOffer([p], s["num_offered"])

  return

  p = get_active()
  randomDiscard(p)

  for i in range(20):
    p = get_active()
    time.sleep(3)
    draw(p)
    randomDiscard(p)

    if random.randint(0,3) == 0:
      query("call_tile", game_id=game_id, player_id=p2, maj=False)
      query("call_tile", game_id=game_id, player_id=p3, maj=False)
      query("call_tile", game_id=game_id, player_id=p4, maj=False)
      time.sleep(3)
      query("end_call_phase", game_id=game_id, player_id=p2, tiles=sendTiles(randomTiles(p2,1)))
      query("end_call_phase", game_id=game_id, player_id=p3, tiles=sendTiles(randomTiles(p3,2)))
      query("end_call_phase", game_id=game_id, player_id=p4, tiles=sendTiles(randomTiles(p4,3)))

if __name__=="__main__":
  main()
