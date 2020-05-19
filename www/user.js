//https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/response
function query(endpoint, params, callback) {
  var xhr = new XMLHttpRequest();

  xhr.onreadystatechange = function() {
    if (xhr.readyState === 4) {
      try {
        var jsn = JSON.parse(xhr.response);
      } catch(e) {
        console.log(xhr.response);
        alert("Server error");
        return;
      }
      callback(jsn);
    }
  }
	xhr.onerror = function() {
		console.log(xhr);
		alert("Network error");
	}

  var joined = "";
	for(key in params) {
    joined += encodeURIComponent(key) + "=" + encodeURI(params[key]);
    joined += "&";
	}
	var url = "http://localhost:5000/"+endpoint+"?"+joined;
  xhr.open('GET', url, true);
  xhr.send('');
}

// https://stackoverflow.com/questions/1349404/generate-random-string-characters-in-javascript
function makeid(length) {
   var result           = '';
   var characters       = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
   var charactersLength = characters.length;
   for ( var i = 0; i < length; i++ ) {
      result += characters.charAt(Math.floor(Math.random() * charactersLength));
   }
   return result;
}

var cache = {};
function getImage(url) {
  if(cache[url]) {
    return cache[url];
  } else {
    var img = document.createElement("img");
    img.src = url;
    cache[url] = img;
    img.onload = function() {
      img.is_ready = true;
    }
    return img;
  }
}

function Game(game_id, player_id) {
  function Tile(tile_str, x, y, width){
    var that = this;
    var t = tile_str.split(":");
    var img = getImage("tiles/" + t[0] + ".png");
    var height = scaleTile(width);
    this.tid = t[1];
    this.str = tile_str;

    this.getX = function() {
      return x;
    }

    this.getY = function() {
      return y;
    }

    this.centerX = function() {
      return x + width/2;
    }

    this.centerY = function() {
      return y + height/2;
    }

    this.render = function() {
      if(img.is_ready) {
        ctx.drawImage(img, x, y, width, height);
      } else {
        ctx.setLineDash([1,1]);
        ctx.strokeStyle='#000';
        ctx.strokeRect(x, y, width, height);
      }
    }

    this.contains = function(xx, yy) {
      return xx >= x && xx <= (x+width) &&
             yy >= y && yy <= (y+height);
    }
  }

  function DropTarget(x, y, width, callback) {
    var that = this;
    var height = scaleTile(width);
    this.contains = function(xx, yy) {
      return xx >= x && xx <= (x+width) &&
             yy >= y && yy <= (y+height);
    }
    this.callback = callback;
    this.render = function() {
      ctx.setLineDash([1,1]);
      ctx.strokeStyle='#000';
      ctx.strokeRect(x, y, width, height);
    }
  }

  function Button(id, x, y, width, height, text, selected, callback) {
    var that = this;
    this.contains = function(xx, yy) {
      return xx >= x && xx <= (x+width) &&
             yy >= y && yy <= (y+height);
    }
    this.mousedown = function(xx, yy) {
      if(that.contains(xx, yy)) {
        pressed_btn = id;
      }
    }
    this.mouseup = function(xx, yy) {
      if(that.contains(xx, yy) && pressed_btn === id) {
        that.callback();
      }
      start_press = false;
    }
    this.callback = callback;
    this.render = function() {
      if(selected) {
        ctx.fillStyle = '#F00';
      } else if (that.contains(mx, my)) {
        ctx.fillStyle = '#BBB';
      } else {
        ctx.fillStyle = '#CCC';
      }
      ctx.fillRect(x, y, width, height);
      var twid = ctx.measureText(text).width;
      drawText(text, "button", x+width*0.5-twid*0.5, y+height*0.5+7);
    }
  }

  console.log("Game object created.");
  var that = this;
  this.state = null;
  this.error = null;

  var canvas = document.getElementById("canvas");
  var ctx = canvas.getContext("2d");
  var wid = 1;
  var hei = 1;
  var tileWidth = 1;
  var tileHeight = 1;
  var tiles = [];
  var drag_tile = null;
  var drag_tile_obj = null
  var mx = 0;
  var my = 0;
  var mx_base = 0;
  var my_base = 0;
  var tx_base = 0;
  var ty_base = 0;
  var drop_targets = [];
  var buttons = [];
  var pressed_btn = null;

  function init() {
    that.rescale();

    canvas.addEventListener('mousedown', function(e) {
      that.mousedown(e.offsetX, e.offsetY);
    });

    canvas.addEventListener('mousemove', function(e) {
      that.mousemove(e.offsetX, e.offsetY);
    });

    window.addEventListener('mouseup', function(e) {
      that.mouseup(e.offsetX, e.offsetY);
    });
  }

  this.rescale = function() {
    if(Math.abs(document.documentElement.clientWidth-wid) > 2 ||
       Math.abs(document.documentElement.clientHeight-hei) > 2) {
      wid = document.documentElement.clientWidth;
      hei = document.documentElement.clientHeight;
      canvas.width = wid;
      canvas.height = hei;

      tileWidth = Math.min(wid / 14, 197);
      tileHeight = scaleTile(tileWidth);
    }
  }

  this.render = function() {
    if(!that.state) {
      return;
    }
    var phase = that.state.phase;
    clear();
    showPlayers();
    showDragTile();
    showHand();
    showLog();
    showSuggestTrade();
    showDiscard();
    showMainButtons();
    drawText("Your name: " + player_name(that.state.player_idx), "player_name", wid/2, 15);
    if(phase == "TRADING_MANDATORY" || phase == "TRADING_OPTIONAL_EXECUTE") {
      showOffer();
    }
    if(drag_tile_obj) {
      drag_tile_obj.render();
    }
    if(phase == "WAITING_PLAYERS") {
      mainText("Waiting for players.");
    } else if(phase == "TRADING_MANDATORY") {
      var dirs = [1, 2, -1, -1, 2, 1]
      var dirStrs = ["right", "across", "left", "left", "across", "right"];
      var trades = that.state.trades;
      var dirStr = dirStrs[trades];
      var dir = dirs[trades];
      var nextp = player_name(that.state.player_idx + dir);
      mainText("Select three tiles to pass " + dirStr + " to " + nextp + ".");
    } else if(phase == "TRADING_OPTIONAL_SUGGEST") {
      var nextp = player_name(that.state.player_idx + 2);
      mainText("Offer how many tiles to " + nextp + "?");
    } else if(phase == "TRADING_OPTIONAL_EXECUTE") {
      var nextp = player_name(that.state.player_idx + 2);
      var num = that.state.num_offered;
      if(num > 0) {
        var nextp = player_name(that.state.player_idx + 2);
        mainText("Select " + num + " tile(s) to pass across to " + nextp + ".");
      } else {
        mainText("Waiting for other players to pass.");
      }
    } else if (phase == "DISCARD") {
      if(that.state.your_turn) {
        mainText("Discard a tile.")
      } else {
        var nextp = player_name(that.state.next_player);
        mainText("Waiting for " + nextp + " to discard.");
      }
    } else if (phase == "START_TURN") {
      if(that.state.your_turn) {
        if(that.state.timeout_elapsed || that.state.all_wavied) {
          mainText("Call or draw?");
        }
      } else if(that.state.can_call_maj[that.state.player_idx]) {
        mainText("Call?");
      } else {
        mainText("Waiting for " + player_name(that.state.next_player));
      }
    } else {
      mainText(that.state.phase);
    }
  }

  function player_name(idx) {
    var pnames = that.state.player_names;
    var len = pnames.length;
    var i = idx % len;
    if(i < 0) {
      i += len;
    }
    return pnames[i];
  }

  function clear() {
    ctx.fillStyle = "#FFF";
    ctx.fillRect(0, 0, wid, hei);
    tiles = [];
    drop_targets = [];
    buttons = [];
  }

  function showLog() {
    var log = that.state.log;
    var logWidth = 350;
    drawText("Game Log", "log_title", wid-logWidth, 15);
    for(var i = 0; i < log.length; i++) {
      drawText(log[i][1], "log", wid - logWidth, i*15+30);
    }
  }

  function showPlayers() {
    var pl = that.state.player_names;
    var phase = that.state.phase;
    drawText("Players", "heading", 0, 15);
    for(var i = 0; i < pl.length; i++) {
      var typ = "name";
      if(i == that.state.next_player && ["DISCARD","START_TURN","PENDING_CALL"].indexOf(phase) !== -1) {
        typ = "bold_name";
      }
      var name = pl[i];
      if(i == 0 && phase != "WAITING_PLAYERS") {
        name += " (East)";
      }
      drawText(name, typ, 0, 20*i+40);
    }
  }

  function showSuggestTrade() {
    if(that.state.phase == "TRADING_OPTIONAL_SUGGEST") {
      var buttonWidth = 100;
      for(let i = 0; i <= 3; i++) {
        var x = wid/2 + buttonWidth * (i-2);
        var y =  hei*0.25 + 50;
        var sel = (i == that.state.num_offered);
        var id = "suggestTrade" + i;
        var btn = new Button(id, x, y, buttonWidth-10, 40, ""+i, sel, function() {
          that.state.num_offered = i;
          gquery("suggest_trade", {"num_offered": i});
        });
        btn.render();
        buttons.push(btn);
      }
    }
  }

  function showDragTile() {
    if(drag_tile) {
      var tile = new Tile(drag_tile, (mx-mx_base)+tx_base,
        (my-my_base)+ty_base, tileWidth);
      drag_tile_obj = tile;
    } else {
      drag_tile_obj = null;
    }
  }

  function showHand() {
    var h = that.state.hand;
    var x = 0;
    for(let i = 0; i < h.length + 1; i++) {
      if(h[i] != drag_tile) {
        var y = hei-tileHeight;

        var drop_target = new DropTarget(x, y, tileWidth, function(drag_tile) {
          insertTile(drag_tile, i);
        });

        if(drag_tile_obj && drop_target.contains(
          drag_tile_obj.centerX(), drag_tile_obj.centerY())) {
          drop_target.render();
          drop_targets.push(drop_target);
          x += tileWidth;
        }

        if(i < h.length) {
          var tile = new Tile(h[i], x, y, tileWidth);
          tile.render();
          tiles.push(tile);
        }

        x += tileWidth;
      }
    }
  }

  function showOffer() {
    var phase = that.state.phase;
    var num_offer = that.state.num_offered;
    if((phase == "TRADING_OPTIONAL_EXECUTE" && num_offer > 0) ||
       phase == "TRADING_MANDATORY") {
      if(num_offer === null) {
        num_offer = 3;
      }

      var x = wid/2 - num_offer/2*tileWidth;
      var y = hei - tileHeight*2.5;
      var off = that.state.offered;
      for(let i = 0; i < num_offer; i++) {
        var drop_target = new DropTarget(x, y, tileWidth, function(drag_tile) {
          offerTile(drag_tile, i);
        });
        drop_target.render();
        drop_targets.push(drop_target);

        if (i<off.length && off[i] != drag_tile) {
          var tile = new Tile(off[i], x, y, tileWidth);
          tile.render();
          tiles.push(tile);
        }
        x += tileWidth;
      }
    }
  }

  function showDiscard() {
    var phase = that.state.phase;
    var x = wid/2 - 0.5*tileWidth;
    var y = hei - tileHeight*2.5;
    if(phase == "DISCARD" && that.state.your_turn) {
      var drop_target = new DropTarget(x, y, tileWidth, function(drag_tile) {
        that.state.hand = removeTile(that.state.hand, drag_tile);
        gquery("discard_tile", {"tile": sendTiles([drag_tile])});
      });
      drop_target.render();
      drop_targets.push(drop_target);
    } else if(phase=="START_TURN" && that.state.top_discard) {
      var tile = new Tile(that.state.top_discard, x, y, tileWidth);
      tile.render();
    }
  }

  function showMainButtons() {
    var btnIds = [];
    if((that.state.phase == "START_TURN" || that.state.phase == "PENDING_CALL")) {
      if (that.state.can_call[that.state.player_idx]) {
        btnIds.push("call");
      }
      if (that.state.can_call_maj[that.state.player_idx]) {
        btnIds.push("call_maj");
        if(!that.state.your_turn){
          btnIds.push("waive");
        }
      }
    }
    if(that.state.phase == "START_TURN" && that.state.your_turn) {
      btnIds.push("draw");
    }
    var btns = {
      "draw": {
        "text": "Draw",
        "callback": function() {
          // TODO: queue until able
          gquery("draw_tile", {});
        }
      },
      "call": {
        "text": "Call",
        "callback": function() {
          gquery("call_tile", {"maj": false});
        }
      },
      "call_maj": {
        "text": "Call & Maj",
        "callback": function() {
          gquery("call_tile", {"maj": true});
        }
      },
      "waive": {
        "text": "Don't Call",
        "callback": function() {
          gquery("waive_call", {});
        }
      },
    };
    var buttonWidth = 120;
    for(var i = 0; i < btnIds.length; i++) {
      var x = wid/2 + buttonWidth * (i-btnIds.length/2);
      var y =  hei*0.25 + 50;
      var id = btnIds[i];
      var data = btns[id];
      var btn = new Button(id, x, y, buttonWidth-10, 40,
        data.text, false, data.callback);
      btn.render();
      buttons.push(btn);
    }
  }

  function mainText(text) {
    drawText(text, "main", wid/2, hei*0.25);
  }

  function scaleTile(width) {
    return width/179*240;
  }

  function drawText(text, type, x, y) {
    if(type == "main") {
      ctx.font = "30px Arial";
      ctx.textAlign = "center";
    } else if(type == "heading") {
      ctx.font = "17px Arial";
      ctx.textAlign = "left";
    } else if(type == "name") {
      ctx.font = "15px Arial";
      ctx.textAlign = "left";
    } else if(type == "log") {
      ctx.font = "15px Arial";
      ctx.textAlign = "left";
    } else if(type == "bold_name") {
      ctx.font = "bold 15px Arial";
      ctx.textAlign = "left";
    } else if(type == "button") {
      ctx.font = "20px Arial";
      ctx.textalign = "left";
    } else if(type == "player_name") {
      ctx.font = "17px arial";
      ctx.textAlign = "center";
    } else if(type == "log_title") {
      ctx.font = "bold 15px Arial";
      ctx.textAlign = "left";
    } else {
      ctx.font = "8px Arial";
    }
    ctx.fillStyle = "#000";
    ctx.fillText(text, x, y);
  }

  function removeTile(tiles, choice) {
    var res = [];
    for(var i = 0; i < tiles.length; i++) {
      if(tiles[i] != choice) {
        res.push(tiles[i]);
      }
    }
    return res;
  }

  function insertTile(drag_tile, pos) {
    var h = that.state.hand;
    var new_order = [];
    for(var i = 0; i <= h.length; i++) {
      if(i == pos) {
        new_order.push(drag_tile);
      }
      if(i < h.length && h[i] != drag_tile) {
        new_order.push(h[i]);
      }
    }
    that.state.offered = removeTile(that.state.offered, drag_tile);
    that.state.hand = new_order;
    gquery("rearrange_tiles", {"tiles": sendTiles(new_order)});
  }

  function offerTile(drag_tile, pos) {
    var off = that.state.offered;
    if(pos < off.length) {
      off[pos] = drag_tile;
    } else {
      off.push(drag_tile);
    }
    that.state.hand = removeTile(that.state.hand, drag_tile);

    gquery("offer_tiles", {"tiles": sendTiles(off)});
  }

  this.loadState = function() {
    gquery("game_state", {});
  }

  function sendTiles(tiles) {
    var res = [];
    for(var i = 0; i < tiles.length; i++) {
      res.push(tiles[i].split(":")[1]);
    }
    return res.join(",");
  }

  function gquery(endpoint, data) {
    data["game_id"] = game_id;
    data["player_id"] = player_id;
    query(endpoint, data, that.recvState);
  }

  this.recvState = function(data) {
    if(data.error) {
      console.log(data.error);
      that.error = data.error;
    } else {
      that.state = data;
    }
  }

  this.mousedown = function(x,y) {
    for(var i = 0; i < tiles.length; i++) {
      if(tiles[i].contains(x,y)) {
        drag_tile = tiles[i].str;
        mx_base = x;
        my_base = y;
        tx_base = tiles[i].getX();
        ty_base = tiles[i].getY();
      }
    }
    for(var i = 0; i < buttons.length; i++) {
      buttons[i].mousedown(x, y);
    }
  }

  this.mousemove = function(x,y) {
    mx = x;
    my = y;
  }

  this.mouseup = function(x,y) {
    if (drag_tile_obj) {
      var xx = drag_tile_obj.centerX();
      var yy = drag_tile_obj.centerY();
      for (var i = 0; i < drop_targets.length; i++) {
        if (drop_targets[i].contains(x,y)) {
          drop_targets[i].callback(drag_tile);
        }
      }
    }
    drag_tile = null;
    for(var i = 0; i < buttons.length; i++) {
      buttons[i].mouseup(x, y);
    }
    pressed_btn = null;
  }

  init();
}

function init() {
  console.log("Init");
  var q = window.location.search.substring(1);
  var parts = q.split("&");
  var game_id = null;
  var player_id = null;
  for(var i = 0; i < parts.length; i++) {
    var kv = parts[i].split("=");
    if(kv[0] == "game_id") {
      game_id = kv[1];
    } else if (kv[0] == "player_id") {
      player_id = kv[1];
    }
  }

  if (game_id == null) {
    query("create_game", {}, function(data) {
      document.location.href = "/?game_id=" + encodeURIComponent(data["game_id"]);
    });
    return;
  }

  if (player_id == null) {
    player_id = localStorage.getItem("player_id");
  }
  if (!player_id) {
    player_id = makeid(16);
    localStorage.setItem("player_id", player_id);
  }

  var player_name = localStorage.getItem("player_name");
  if (!player_name) {
    player_name = prompt("Enter nickname:");
    localStorage.setItem("player_name", player_name);
  }

  var game = new Game(game_id, player_id);
  query("add_player", {"game_id": game_id, "player_id": player_id, "player_name": player_name}, game.recvState);

  // debug
  window.game = game;

	setInterval(function(){game.render()}, 30);
	setInterval(function(){game.loadState()}, 1000);
	setInterval(function(){game.rescale()}, 3000);
}
