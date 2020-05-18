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
    joined += encodeURIComponent(key) + "=" + encodeURIComponent(params[key]);
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
  var selected = [];

  function init() {
    that.rescale();
  }

  this.rescale = function() {
    if(Math.abs(document.documentElement.clientWidth-wid) > 2 ||
       Math.abs(document.documentElement.clientHeight-hei) > 2) {
      wid = document.documentElement.clientWidth;
      hei = document.documentElement.clientHeight;
      canvas.width = wid;
      canvas.height = hei;

      tileWidth = Math.min(wid / 13, 197);
      tileHeight = scaleTile(tileWidth);
    }
  }

  this.render = function() {
    if(!that.state) {
      return;
    }
    clear();
    showPlayers();
    showHand();
    if(that.state.phase == "WAITING_PLAYERS") {
      mainText("Waiting for players.");
    } else {
      mainText(that.state.phase);
    }
  }

  function clear() {
    ctx.fillStyle = "#FFF";
    ctx.fillRect(0, 0, wid, hei);
  }

  function showPlayers() {
    var pl = that.state.player_names;
    drawText("Players", "heading", 0, 15);
    for(var i = 0; i < pl.length; i++) {
      var typ = "name";
      if(i == that.state.next_player && ["DISCARD","START_TURN","PENDING_CALL"].indexOf(that.state.phase) !== -1) {
        typ = "bold_name";
      }
      var name = pl[i];
      if(i == 0) {
        name += " (East)";
      }
      drawText(name, typ, 0, 20*i+40);
    }
  }

  function showHand() {
    var h = that.state.hand;
    for(var i = 0; i < h.length; i++) {
      renderTile(h[i], i*tileWidth, hei-tileHeight, tileWidth);
    }
  }

  function mainText(text) {
    drawText(text, "main", wid/2, hei/2);
  }

  function scaleTile(width) {
    return width/179*240;
  }

  function renderTile(tile, x, y, width) {
    var t = tile.split(":")[0];
    var img = getImage("tiles/" + t + ".png");
    var height = scaleTile(width);
    if(img.is_ready) {
      ctx.drawImage(img, x, y, width, height);
    } else {
      ctx.strokeStyle='#000';
      ctx.strokeRect(x, y, width, height);
    }
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
    } else if(type == "bold_name") {
      ctx.font = "bold 15px Arial";
      ctx.textAlign = "left";
    } else {
      ctx.font = "8px Arial";
    }
    ctx.fillStyle = "#000";
    ctx.fillText(text, x, y);
  }

  this.loadState = function() {
    query("game_state", {"game_id": game_id, "player_id": player_id}, that.recvState);
  }

  this.recvState = function(data) {
    if(data.error) {
      console.log(data.error);
      that.error = data.error;
    } else {
      that.state = data;
    }
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
