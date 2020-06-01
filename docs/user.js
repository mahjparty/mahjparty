var alertCount = localStorage.getItem("alert_count") || 0;
var host = localStorage.getItem("host") || ("https://api.mahj.party");

//https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/response
function query(endpoint, params, callback) {
  var xhr = new XMLHttpRequest();

  xhr.onreadystatechange = function() {
    if (xhr.readyState === 4) {
      try {
        var jsn = JSON.parse(xhr.response);
      } catch(e) {
        console.log(xhr.response);
        if(alertCount > 0) {
          alert("Server error");
          alertCount--;
        }
        return;
      }
      callback(jsn);
    }
  }
  xhr.onerror = function() {
    console.log(xhr);
    if(alertCount > 0) {
      alert("Network error");
      alertCount--;
    }
  }

  var joined = "";
	for(key in params) {
    joined += encodeURIComponent(key) + "=" + encodeURI(params[key]);
    joined += "&";
	}
	var url = host+"/"+endpoint+"?"+joined;
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

var tile_data = {
  "O": {
    "desc": "Dot",
    "type": "numerical"
  },
  "B": {
    "desc": "Bam",
    "type": "numerical"
  },
  "C": {
    "desc": "Crak",
    "type": "numerical"
  },
  "W": {
    "desc": "Wind",
    "type": "named",
    "named": ["East", "South", "West", "North"]
  },
  "D": {
    "desc": "Dragon",
    "type": "named",
    "named": ["Red", "Green", "Soap"]
  },
  "F": {
    "desc": "Flower",
    "type": "equivalent"
  },
  "J": {
    "desc": "Joker",
    "type": "equivalent"
  }
};

function niceName(tile_str) {
  var data = tile_data[tile_str.charAt(0)];
  var type = data["type"];
  var num = Number(tile_str.charAt(1));
  if(type == "numerical") {
    return num + " " + data["desc"];
  } else if(type == "named") {
    return data["named"][num-1];
  } else if(type == "equivalent") {
    return data["desc"];
  } else {
    return tile_str;
  }
}

function shortName(tile_str) {
  var data = tile_data[tile_str.charAt(0)];
  var type = data["type"];
  var num = Number(tile_str.charAt(1));
  if(type == "numerical") {
    return "" + num;
  } else if(type == "named") {
    return data["named"][num-1].charAt(0);
  } else if(type == "equivalent") {
    return data["desc"].charAt(0);
  } else {
    return tile_str.charAt(0);
  }
}

function Game(game_id, player_id) {
  function Tile(tile_str, x, y, width){
    var that = this;
    var t = tile_str.split(":");
    var img = getImage("/tiles/" + t[0] + ".png");
    var blank = getImage("/tiles/blank.png");
    var height = scaleTile(width);
    this.tid = t[1];
    this.str = tile_str;
    this.draggable = true;
    this.zoomable = false;

    this.getX = function() {
      return x;
    }

    this.getY = function() {
      return y;
    }

    this.getWidth = function() {
      return width;
    }

    this.centerX = function() {
      return x + width*0.5;
    }

    this.centerY = function() {
      return y + height*0.5;
    }

    this.render = function() {
      drawTile(t[0], x, y, width, height);
    }

    function drawTile(t0, x, y, width, height) {
      var style = "small_tile";
      if(t0.charAt(0) == "O") {
        style = "small_blue";
      } else if(t0.charAt(0) == "B") {
        style = "small_green";
      } else if(t0.charAt(0) == "C") {
        style = "small_red";
      } else if(t0.charAt(0) == "W") {
        style = "small_tile";
      } else if(["D","J","F"].indexOf(t0.charAt(0)) !== -1) {
        style = null;
      }
      var textOnly = (style !== null) && showTileName;
      var im = textOnly ? blank : img;
      tryDrawImage(im, x, y, width, height);
      if(textOnly) {
        if(img.is_ready) {
          ctx.drawImage(img, 20, 55, 127, 169, x+width*0.1, y+height*0.42, width*0.48, height*0.48);
        }
        drawText(that.shortName(), style, x+width*0.66, y+height*0.5, width*0.34, height*0.34);
      }
    }

    function tryDrawImage(im, x, y, width, height) {
      if(im.is_ready) {
        ctx.drawImage(im, x, y, width, height);
      } else {
        ctx.setLineDash([1,1]);
        ctx.lineWidth=1;
        ctx.strokeStyle='#000';
        ctx.strokeRect(x, y, width, height);
      }
    }

    this.hoverRender = function(xx, yy, twid) {
      if(this.contains(xx,yy) && img.is_ready) {
        var thei = scaleTile(twid);
        var newx = x+width/2-twid/2;
        var newy = y+width/2-thei/2;
        newx = Math.min(Math.max(newx, 0), wid-twid);
        newy = Math.min(Math.max(newy, 0), hei-thei);
        drawTile(t[0], newx, newy, twid, thei);
      }
    }

    this.name = function() {
      return niceName(tile_str);
    }

    this.shortName = function() {
      return shortName(tile_str);
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
      ctx.lineWidth=1;
      ctx.strokeStyle='#111';
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
    }
    this.callback = callback;
    this.render = function(typ) {
      if(selected || (pressed_btn == id)) {
        ctx.fillStyle = '#F00';
      } else if (that.contains(mx, my)) {
        ctx.fillStyle = '#BBB';
      } else {
        ctx.fillStyle = '#CCC';
      }
      ctx.fillRect(x, y, width, height);
      var text_type = typ || "button";
      var ht = (text_type == "button") ? 14 : 10;
      drawText(text, text_type, x+width*0.5, y+height*0.5+ht*0.5);
    }
  }

  console.log("Game object created.");
  var that = this;
  this.state = null;
  this.error = null;
  this.errorTime = null;

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
  var pending_action = null;
  var tileData = null;
  var override_drag_obj = null;
  var pname = localStorage.getItem("player_name") || "";
  var words = null;
  var actionTime = null; // suppress state updates when action was taken recently
  var actionDuration = 1.0;
  var exit = false;
  var showTileName = (localStorage.getItem("show_tile_name") != "false");

  var buttonWidth = 160;
  var logWidth = 450;
  var numLogs = 10;
  var logLineHeight = 15;
  var logHeight = logLineHeight*numLogs+25;
  var mainTextHeight = 1;
  var logDuration = null; //disabled
  var errorDuration = 10;
  var firstLoad = true;

  var startupHash = null;

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

    canvas.addEventListener('touchstart', function(e) {
      var touch = e.touches[0];
      if(touch) {
        that.mousedown(touch.pageX, touch.pageY);
      }
      e.preventDefault();
    });

    canvas.addEventListener('touchmove', function(e) {
      var touch = e.touches[0];
      if(touch) {
        that.mousemove(touch.pageX, touch.pageY);
      }
      e.preventDefault();
    });

    window.addEventListener('touchend', function(e) {
      var touch = e.changedTouches[0];
      if(touch) {
        that.mouseup(touch.pageX, touch.pageY);
      }
      e.preventDefault();
    });
  }

  function centerX() {
    return (wid-logWidth)*0.5;
  }

  this.rescale = function() {
    if(Math.abs(document.documentElement.clientWidth-wid) > 2 ||
       Math.abs(document.documentElement.clientHeight-hei) > 2) {
      wid = document.documentElement.clientWidth;
      hei = document.documentElement.clientHeight;
      canvas.width = wid;
      canvas.height = hei;

      tileWidth = Math.min((wid-logWidth) / 14.11, 197);
      tileHeight = scaleTile(tileWidth);

      mainTextHeight = scaleTile(tileWidth*0.5)*5+20;

    }
  }

  this.render = function() {
    clear();
    showStartup();

    if(!that.state) {
      return;
    }
    if(exit) {
      return;
    }
    checkPendingAction();

    showDragTile();
    showDiscardPile();
    showHand();
    showSidePanel();
    showPlayers();
    showLog();
    showSuggestTrade();
    showDiscard();
    showMainButtons();
    showOffer();
    var tile_name = showHover();
    showMetadata(tile_name);
    showMainText();
    if(drag_tile_obj) {
      if(override_drag_obj) {
        override_drag_obj.render();
      } else {
        drag_tile_obj.render();
      }
    }
  }

  function isDisqualified() {
    return that.state.disqualified[that.state.player_idx];
  }

  function now() {
    return (+new Date())*0.001;
  }

  function showStartup() {
    var joinUrl = document.getElementById("joinUrl");
    var phase = null;
    if(that.state !== null) {
      phase = that.state.phase;
    } else if(firstLoad) {
      phase = "LOADING";
    } else if(game_id === null) {
      phase = "CREATE_GAME";
    } else {
      phase = "STARTUP";
    }

    if(phase == "CREATE_GAME") {
      words = joinUrl.value;
    } else if(phase == "STARTUP") {
      if(pname !== joinUrl.value) {
        pname = joinUrl.value;
        localStorage.setItem("player_name", pname);
      }
    }

    function validWords(w) {
      var sp = (w || "").split(" ");
      if(sp.length != 4) {
        return false;
      }
      var valid = (sp.length == 4);
      for(var i = 0; i < sp.length; i++) {
        if(sp[i].length < 3) {
          return false;
        }
      }
      return true;
    }

    function lookupWords(w) {
      if(validWords(w)) {
        query("lookup_game", {"words": w}, function(data) {
          if(data.error) {
            console.log(data.error);
            that.error = data.error;
            that.errorTime = now();
          } else {
            document.location.href = "/?g=" + encodeURIComponent(data["game_id"]);
          }
        });
      }
    }

    var newHash = phase + "," + centerX() + "," + mainTextHeight;
    if(phase == "LOADING") {
      drawText("Loading Mahj Party...", "supermain", wid/2, mainTextHeight);
    } else if(phase == "CREATE_GAME") {
      drawText("It's Mahj Party Time!", "supermain", wid/2, mainTextHeight);

      var errOffset = 190;
      if(that.error && that.errorTime && (now()-that.errorTime) < errorDuration) {
        drawText(that.error, "main", wid/2, mainTextHeight+errOffset);
      } else {
        drawText("Or join an existing game by entering the four code words:", "main", wid/2, mainTextHeight+errOffset);
      }

      var btnWid = 200;
      var btn1 = new Button("create_game", wid*0.5-btnWid*0.5, mainTextHeight+50, btnWid, 60,
        "Create New Game", false, function() {
        query("create_game", {}, function(data) {
          document.location.href = "/?g=" + encodeURIComponent(data["game_id"]);
        });
      });
      btn1.render();
      buttons.push(btn1);

      if(validWords(words)) {
        var btn2 = new Button("lookup_game", wid*0.5-btnWid*0.5, mainTextHeight+250, btnWid, 60,
          "Join Game", false, function() {
            lookupWords(words);
        });
        btn2.render();
        buttons.push(btn2);
      }
    } else if(phase == "STARTUP") {
      drawText("Ready to play Mahj?",
        "supermain", wid/2, mainTextHeight-50);
      if(that.error && that.errorTime && (now()-that.errorTime) < errorDuration) {
        drawText(that.error, "main", wid/2, mainTextHeight);
      } else {
        drawText("Choose a nickname!", "main", wid/2, mainTextHeight);
      }
      var btnWid = 200;
      var btn = new Button("join", wid*0.5-btnWid*0.5, mainTextHeight+200, btnWid, 60,
        "Join Game", false, function() {
        gquery("add_player", {"player_name": pname});
      });
      btn.render();
      buttons.push(btn);
    }
    else if(phase == "WAITING_PLAYERS") {
      drawText("Copy this link and send it to your friends to let them join!",
        "sub", centerX(), mainTextHeight+200);
      var img = getImage("/img/up-arrow.png");
      if(img.is_ready) {
        var w = 50;
        var h = w/img.width*img.height;
        ctx.drawImage(img, centerX()-w*0.5, mainTextHeight+115, w, h);
      }
      drawText("Or join using the following code words:",
        "sub", centerX(), mainTextHeight+250);
      drawText(that.state.words_full,
        "bold_sub", centerX(), mainTextHeight+275);
    }
    if(newHash != startupHash) {
      var joinWidth = 600;
      if(phase == "CREATE_GAME") {
        joinUrl.style.display="block";
        joinUrl.value = words || "";
        joinUrl.style.left = (wid*0.5 - joinWidth*0.5) + "px";
        joinUrl.style.top = (mainTextHeight+200) + "px";
        joinUrl.style.width = joinWidth + "px";
        joinUrl.style.fontSize = "2rem";
        joinUrl.maxLength = 100;
        joinUrl.onmousedown = null;
        joinUrl.onkeypress = function(e) {
          if(e.keyCode == 13) {
            lookupWords(words);
          }
        }
      } else if(phase == "STARTUP") {
        joinUrl.style.display="block";
        joinUrl.value = pname;
        joinUrl.style.left = (wid*0.5 - joinWidth*0.5) + "px";
        joinUrl.style.top = (mainTextHeight+50) + "px";
        joinUrl.style.width = joinWidth + "px";
        joinUrl.style.fontSize = "2rem";
        joinUrl.maxLength = 20;
        joinUrl.onmousedown = null;
        joinUrl.onkeypress = function(e) {
          if(e.keyCode == 13) {
            gquery("add_player", {"player_name": pname});
          }
        }
      } else if(phase == "WAITING_PLAYERS") {
        joinUrl.style.display="block";
        joinUrl.maxLength = null;
        joinUrl.value = document.location.href;
        joinUrl.style.left = (centerX() - joinWidth*0.5) + "px";
        joinUrl.style.top = (mainTextHeight+70) + "px";
        joinUrl.style.width = joinWidth + "px";
        joinUrl.style.fontSize = "1.5rem";
        joinUrl.onchange = null;
        joinUrl.onmousedown = function(e) {
          // https://www.w3schools.com/howto/howto_js_copy_clipboard.asp
          joinUrl.select();
          joinUrl.setSelectionRange(0, 99999);
          document.execCommand("copy");
        };
        joinUrl.onkeypress = null;
      } else {
        joinUrl.style.display="none";
      }
      startupHash = newHash;
    }
  }

  function getRem() {
    return Math.ceil(that.state.timeout_deadline-now());
  }

  function showMainText() {
    var phase = that.state.phase;

    var log = that.state.log;
    if(that.error && that.errorTime && (now()-that.errorTime) < errorDuration) {
      subText(that.error);
    } else {
      if(log.length >= 1) {
        var lastLog = log[log.length-1];
        if(logDuration == null || now() - lastLog[0] < logDuration) {
          subText(lastLog[1]);
        }
      }
    }

    if(isDisqualified()) {
      mainText("Mahj retracted.");
    } else if(phase == "WAITING_PLAYERS") {
      var np = that.state.player_names.length;
      if(np == 3) {
        mainText("Waiting for 1 more player.");
      } else {
        mainText("Waiting for " + (4-np) + " more players.");
      }
    } else if(phase == "TRADING_MANDATORY") {
      var dirs = [1, 2, -1, -1, 2, 1]
      var dirStrs = ["right", "across", "left", "left", "across", "right"];
      var trades = that.state.trades;
      var dirStr = dirStrs[trades];
      var dir = dirs[trades];
      if(that.state.commit_offered) {
        mainText("Waiting for other players to pass " + dirStr + ".");
      } else {
        var nextp = player_name(that.state.player_idx + dir);
        mainText("Select three tiles to pass " + dirStr + " to " + nextp + ".");
      }
    } else if(phase == "TRADING_OPTIONAL_SUGGEST") {
      var nextp = player_name(that.state.player_idx + 2);
      mainText("Offer how many tiles to " + nextp + "?");
    } else if(phase == "TRADING_OPTIONAL_EXECUTE") {
      var nextp = player_name(that.state.player_idx + 2);
      var num = that.state.num_offered;
      if(num > 0 && !that.state.commit_offered) {
        var nextp = player_name(that.state.player_idx + 2);
        mainText("Select " + num + " tile(s) to pass across to " + nextp + ".");
      } else {
        mainText("Waiting for other players to pass.");
      }
    } else if (phase == "DISCARD") {
      if(pending_action == "claim_maj") {
        mainText("Are you sure?");
      } else if(that.state.your_turn) {
        mainText("Discard a tile.")
      } else {
        var nextp = player_name(that.state.next_player);
        mainText("Waiting for " + nextp + " to discard.");
      }
    } else if (phase == "START_TURN") {
      var reason = that.state.can_end_call_phase;
      var rem = getRem();
      var remText = (rem >= 0) ? (" (" + rem + ")") : "";
      var waitReason = null;
      if(reason === null) {
        waitReason = "Waiting for " + player_name(that.state.next_player);
      } else if(reason == "Waiting for calls") {
        waitReason = reason + remText;
      } else {
        waitReason = reason;
      }
      if(that.state.your_turn) {
        if(pending_action == "draw_tile") {
          mainText(waitReason);
        } else if (that.state.top_discard) {
          mainText("Call or draw?");
        } else {
          mainText("Ready to draw?");
        }
      } else {
        if(that.state.your_waive_state == "NONE") {
          if(that.state.can_hold_maj[that.state.player_idx]) {
            mainText("Call?" + remText);
          } else {
            mainText(waitReason);
          }
        } else if (that.state.your_waive_state == "HOLD" ||
                   that.state.your_waive_state == "HOLD_MAJ") {
          mainText("Are you sure?")
        } else if (that.state.your_waive_state == "CALL" ||
                   that.state.your_waive_state == "CALL_MAJ" ||
                   that.state.your_waive_state == "WAIVED") {
          mainText(waitReason);
        } else {
          // Unreachable
          mainText(waitReason);
        }
      }
    } else if (phase == "PENDING_SHOW") {
      if(that.state.your_turn) {
        mainText("Choose tiles to reveal with " + niceName(that.state.called_tile) + ".");
      } else {
        var nextp = player_name(that.state.next_player);
        mainText("Waiting for " + nextp + " to reveal.");
      }
    } else if (phase == "SHOWING_MAJ") {
      if(that.state.your_turn) {
        mainText("Reveal a group.");
      } else {
        var nextp = player_name(that.state.next_player);
        mainText("Waiting for " + nextp + " to reveal mahj.");
      }
    } else if (phase == "WINNER") {
      var nextp = player_name(that.state.next_player);
      mainText(nextp + " won with Mahj!");
    } else if (phase == "WALL") {
      mainText("It's a wall game.");
    } else {
      mainText(that.state.phase);
    }
  }

  function checkPendingAction() {
    var phase = that.state.phase;
    if(phase == "START_TURN" && pending_action == "draw_tile") {
      if(that.state.your_turn) {
        if (that.state.can_end_call_phase === null) {
          gquery("draw_tile", {});
          pending_action = "drawing_tile";
        }
      } else {
        pending_action = null;
      }
    }
    if(phase != "START_TURN" && pending_action == "drawing_tile") {
      pending_action = null;
    }
    if(phase == "START_TURN") {
      if (that.state.can_end_call_phase === null &&
          that.state.call_idx == that.state.player_idx) {
        gquery("end_call_phase", {});
        // temporarily disable end_call_phase from triggering again
        that.state.can_end_call_phase = "Pending";
      }
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
    override_drag_obj = null;
  }

  function showSidePanel() {
    ctx.fillStyle = '#EEE';
    ctx.fillRect(wid-logWidth, 0, logWidth, hei);

    ctx.setLineDash([]);
    ctx.lineWidth=tileWidth*0.03;
    ctx.strokeStyle = '#222';
    ctx.strokeRect(wid-logWidth, 0, logWidth, hei);
  }

  function showLog() {
    var log = that.state.log;
    var base = hei-logHeight+15;
    drawText("Game Log", "heading", wid-logWidth+5, base);
    for(var i = 0; i < log.length && i < numLogs; i++) {
      drawText(log[i][1], "log", wid-logWidth+5, base+i*logLineHeight+15);
    }
  }

  function showMetadata(tile_name) {
    var basex = wid-logWidth+5;
    var basey = hei-logHeight-75;
    drawText("Quick Info", "heading", basex, basey);
    drawText("Player Name: " + player_name(that.state.player_idx), "log", basex, basey+15);
    var txt = "Selected Tile: " + (tile_name || "None");
    drawText(txt, "log", basex, basey+30);
    drawText("Tiles Remaining: " + that.state.deck_size, "log", basex, basey+45);

    var btnText = showTileName ? "Use Chinese Tiles" : "Use English Tiles";
    var btn = new Button("show_tile_name", basex, basey+50, buttonWidth-10, 25, btnText, false, function() {
      showTileName = !showTileName;
      localStorage.setItem("show_tile_name", ""+showTileName);
    });
    btn.render("small_button");
    buttons.push(btn);
  }

  function isJoker(tile_str) {
    return tile_str.charAt(0) == "J";
  }

  function showPlayers() {
    var pl = that.state.player_names;
    var phase = that.state.phase;
    drawText("Players", "heading", wid-logWidth+5, 18);
    var y = 40;
    for(var i = 0; i < pl.length; i++) {
      var typ = "name";
      if(i == that.state.next_player && ["DISCARD","START_TURN"].indexOf(phase) !== -1) {
        typ = "bold_name";
      }
      var name = pl[i];
      var dirs = ["East", "North", "West", "South"];
      if(phase != "WAITING_PLAYERS") {
        name += " (" + dirs[i] + ")";
      }
      var basex = wid-logWidth+5;
      var x = basex;
      drawText(name, typ, x, y);
      if(phase != "WAITING_PLAYERS") {
        y += 5;
        var twid = tileWidth*0.5;
        var thei = scaleTile(twid);
        var board = that.state.boards[i];
        var hasTiles = false;
        for(var j = 0; j < board.length; j++) {
          var group = board[j];
          if(x+group.length*twid >= wid) {
            x = basex;
            y += thei+1;
          }
          for(var k = 0; k < group.length; k++) {
            if(x+twid >= wid) {
              x = basex;
              y += thei+1;
            }
            var jokerSwap = false;
            if(isJoker(group[k]) && drag_tile_obj && that.state.your_turn &&
               (phase == "START_TURN" || phase == "DISCARD")) {
              let stile = sendTiles([drag_tile]);
              let sjoker = sendTiles([group[k]])
              var drop_target = new DropTarget(x, y, twid, function(drag_tile) {
                gquery("swap_joker", {
                  "tile": stile,
                  "joker": sjoker
                });
              });
              if (drop_target.contains(drag_tile_obj.centerX(), drag_tile_obj.centerY())) {
                jokerSwap = true;
              }
            }
            var tile = null;
            if(jokerSwap) {
              override_drag_obj = new Tile(group[k],
                drag_tile_obj.getX(), drag_tile_obj.getY(), drag_tile_obj.getWidth());
              drop_targets.push(drop_target);
            }
            tile = new Tile(group[k], x, y, twid);
            tile.render();
            tile.draggable = false;
            tile.zoomable = true;
            tiles.push(tile);
            x += twid;
            tile.render();
          }

          x += twid*0.2;
          hasTiles = true;
        }
        var rh = that.state.revealed_hands[i];
        if(rh !== null) {
          for(var k = 0; k < rh.length; k++) {
            if(x+twid >= wid) {
              x = basex;
              y += thei+1;
            }
            tile = new Tile(rh[k], x, y, twid);
            tile.render();
            tile.draggable = false;
            tile.zoomable = true;
            tiles.push(tile);
            x += twid;
            tile.render();
          }
          hasTiles = true;
        }
        if(hasTiles) {
          y += thei;
        }
      }
      y += 20;
    }
  }

  function showHover() {
    var tile_name = null;
    if(drag_tile == null) {
      for(var i = 0; i < tiles.length; i++) {
        if(tiles[i].zoomable) {
          tiles[i].hoverRender(mx, my, tileWidth);
        }
        if(tiles[i].contains(mx, my)) {
          tile_name = tiles[i].name();
        }
      }
    } else if(drag_tile_obj) {
      tile_name = drag_tile_obj.name();
    }
    return tile_name;
  }

  function showSuggestTrade() {
    if(that.state.phase == "TRADING_OPTIONAL_SUGGEST") {
      for(let i = 0; i <= 3; i++) {
        var x = centerX() + buttonWidth * (i-2);
        var y =  mainTextHeight + 50;
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
    var y = hei-tileHeight*1.08;
    var rimg = getImage("/img/rack7.jpg");
    var rheight = tileHeight*1.115;
    var slices = 10;
    var sliceHei = rheight*0.007;
    for(var i = slices; i >= 0; i--) {
      var shade = i/slices;
      var r = Math.round(255*shade + 100*(1-shade));
      var g = Math.round(255*shade + 60*(1-shade));
      var b = Math.round(255*shade + 60*(1-shade));
      ctx.fillStyle='rgb('+r+','+g+','+b +')';
      ctx.fillRect(0, hei-rheight-sliceHei*i*0.95, tileWidth*14+i*sliceHei, rheight+i*sliceHei);
    }
    if(rimg.is_ready) {
      ctx.drawImage(rimg, 0, hei-rheight, tileWidth*14, rheight*1.04);
    }

    var h = that.state.hand;
    var x = 0;
    for(let i = 0; i < h.length + 1; i++) {
      if(h[i] != drag_tile) {

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
    if(isDisqualified() || that.state.commit_offered) {
      return;
    }
    var phase = that.state.phase;
    var num_offer = that.state.num_offered;
    if((phase == "TRADING_OPTIONAL_EXECUTE" && num_offer > 0) ||
       phase == "TRADING_MANDATORY") {
      if(num_offer === null) {
        num_offer = 3;
      }

      var x = centerX() - num_offer/2*tileWidth;
      var y = hei - tileHeight*2.5;
      var off = that.state.offered;
      for(let i = 0; i < num_offer; i++) {
        var drop_target = new DropTarget(x, y, tileWidth, function(drag_tile) {
          offerTile(drag_tile, i, false);
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
    } else if((phase == "PENDING_SHOW" || phase == "SHOWING_MAJ")
       && that.state.your_turn) {
      var off = that.state.offered;
      var num_tiles = Math.max(off.length, 1);
      var x = centerX() - num_tiles*0.5*tileWidth;
      var y = hei-tileHeight*2.5;

      var drop_target = new DropTarget(x-tileWidth, y, tileWidth, function(drag_tile) {
        offerTile(drag_tile, 0, true);
      });

      if(drag_tile_obj && drop_target.contains(
        drag_tile_obj.centerX(), drag_tile_obj.centerY())) {
        drop_target.render();
        drop_targets.push(drop_target);
      }


      var force_target = true;
      for(let i = 0; i < off.length + 1; i++) {
        drop_target = new DropTarget(x, y, tileWidth, function(drag_tile) {
          offerTile(drag_tile, i, true);
        });

        if((i == off.length && force_target) ||
          (drag_tile_obj && drop_target.contains(
          drag_tile_obj.centerX(), drag_tile_obj.centerY()))) {
          drop_target.render();
          drop_targets.push(drop_target);
          x += tileWidth;
          force_target = false;
        }

        if(i < off.length &&
           (!drag_tile || off[i] != drag_tile)) {
          var tile = new Tile(off[i], x, y, tileWidth);
          tile.render();
          tiles.push(tile);

          x += tileWidth;
        }
      }
    }
  }

  function showDiscard() {
    if(isDisqualified()) {
      return;
    }
    var phase = that.state.phase;
    var x = centerX() - 0.5*tileWidth;
    var y = hei - tileHeight*2.5;
    if(phase == "DISCARD" && that.state.your_turn) {
      var drop_target = new DropTarget(x, y, tileWidth, function(drag_tile) {
        that.state.hand = removeTile(that.state.hand, drag_tile);
        that.state.top_discard = drag_tile;
        gquery("discard_tile", {"tile": sendTiles([drag_tile])});
      });
      drop_target.render();
      drop_targets.push(drop_target);
    } else if(phase=="START_TURN" && that.state.top_discard) {
      var tile = new Tile(that.state.top_discard, x, y, tileWidth);
      tile.render();
      tile.zoomable = false;
      tile.draggable = false;
      tiles.push(tile);
    }
  }

  function showDiscardPile() {
    var d = that.state.discard_pile;
    if(d.length > 0) {
      var twid = tileWidth / 2;
      var thei = scaleTile(twid);
      drawText("Discard pile", "heading", 5, 15);
      var tilePerRow = Math.floor((wid-logWidth) / twid);
      var x = 0;
      var y = 20;
      for(var i = 0; i < d.length; i++) {
        var tile = new Tile(d[i], x, y, twid);
        tile.render();
        tile.draggable = false;
        tile.zoomable = true;
        tiles.push(tile);
        x += twid;
        if ((i+1) % tilePerRow == 0) {
          x = 0;
          y += thei;
        }
      }
    }
  }

  function showMainButtons() {
    if((pending_action!==null && pending_action!=="claim_maj") || isDisqualified()) {
      return;
    }
    var btnIds = [];
    var phase = that.state.phase;
    if(phase == "START_TURN") {
      if(that.state.can_call[that.state.player_idx]) {
        btnIds.push("empty");
        btnIds.push("confirm_call");
        btnIds.push("waive");
      } else if(that.state.can_call_maj[that.state.player_idx]) {
        btnIds.push("confirm_call_maj");
        btnIds.push("empty");
        btnIds.push("waive");
      } else {
        var waive = false;
        if (that.state.can_hold[that.state.player_idx] && that.state.your_waive_state == "NONE") {
          btnIds.push("hold");
          waive = true;
        }
        if (that.state.can_hold_maj[that.state.player_idx] && that.state.your_waive_state == "NONE") {
          btnIds.push("hold_maj");
          waive = true;
        }
        var draw = that.state.your_turn;
        var ws = that.state.waive_state;
        for(var i = 0; i < ws.length && draw; i++) {
          if(ws[i] == "CALL" || ws[i] == "CALL_MAJ") {
            draw = false;
          }
        }
        if(draw) {
          btnIds.push("draw");
        } else if(waive) {
          btnIds.push("waive");
        }
      }
    } else if(phase == "TRADING_MANDATORY") {
      if(!that.state.commit_offered) {
        if(that.state.offered.length == 3) {
          btnIds.push("commit_offered");
        } else if(that.state.blind_pass_allowed) {
          btnIds.push("blind_pass");
        } else if(that.state.trades == 3 && !that.state.commit_offered &&
                  that.state.offered.length == 0) {
          btnIds.push("skip_passes");
        }
      }
    } else if(phase == "TRADING_OPTIONAL_EXECUTE") {
      if(that.state.offered.length == that.state.num_offered &&
         !that.state.commit_offered && that.state.num_offered > 0) {
        btnIds.push("commit_offered");
      }
    } else if(phase == "PENDING_SHOW") {
      if(that.state.your_turn &&
         that.state.offered.length <= 6 &&
         that.state.offered.length >= 3 &&
         that.state.check_show_tiles === null) {
        btnIds.push("show");
      }
    } else if(phase == "SHOWING_MAJ") {
      if(that.state.your_turn &&
         that.state.offered.length <= 6 &&
         that.state.offered.length >= 1 &&
         that.state.check_show_tiles === null) {
        btnIds.push("show");
      }
    } else if(phase == "DISCARD") {
      if(that.state.your_turn && pending_action == null) {
        btnIds.push("claim_maj");
      }
      if(that.state.your_turn && pending_action == "claim_maj") {
        btnIds.push("confirm_maj");
        btnIds.push("empty");
        btnIds.push("cancel_maj");
      }
    } else if(phase == "WINNER") {
      if(that.state.your_turn) {
        btnIds.push("retract_maj");
      } else if(that.state.revealed_hands[that.state.player_idx] == null) {
        btnIds.push("reveal_hand");
      }
      btnIds.push("new_players");
      btnIds.push("same_players");
    } else if(phase == "WALL") {
      if(that.state.revealed_hands[that.state.player_idx] == null) {
        btnIds.push("reveal_hand");
      }
      btnIds.push("new_players");
      btnIds.push("same_players");
    }
    var btns = {
      "commit_offered": {
        "text": "Pass Tiles",
        "callback": function() {
          gquery("commit_offered", {});
        }
      },
      "blind_pass": {
        "text": "Blind Pass",
        "callback": function() {
          gquery("commit_offered", {});
        }
      },
      "skip_passes": {
        "text": "Stop Charleston",
        "callback": function() {
          gquery("skip_passes", {});
        }
      },
      "draw": {
        "text": "Draw",
        "callback": function() {
          gquery("waive_call", {});
          pending_action = "draw_tile";
        }
      },
      "hold": {
        "text": "Call",
        "callback": function() {
          gquery("place_hold", {"maj": false});
        }
      },
      "hold_maj": {
        "text": "Call & Mahj",
        "callback": function() {
          gquery("place_hold", {"maj": true});
        }
      },
      "confirm_call": {
        "text": "Confirm Call",
        "callback": function() {
          gquery("call_tile", {"maj": false});
        }
      },
      "confirm_call_maj": {
        "text": "Confirm Mahj",
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
      "show": {
        "text": "Reveal",
        "callback": function() {
          gquery("show_tiles",
            {"tiles": sendTiles(that.state.offered)});
          that.state.offered = [];
        }
      },
      "claim_maj": {
        "text": "Claim Mahj",
        "callback": function() {
          pending_action = "claim_maj";
        }
      },
      "confirm_maj": {
        "text": "Confirm Mahj",
        "callback": function() {
          gquery("claim_maj", {});
          pending_action = null;
        }
      },
      "cancel_maj": {
        "text": "Cancel",
        "callback": function() {
          pending_action = null;
        }
      },
      "retract_maj": {
        "text": "Retract Mahj",
        "callback": function() {
          gquery("retract_maj", {});
        }
      },
      "new_players": {
        "text": "New Players",
        "callback": function() {
          document.location.href="/";
        }
      },
      "same_players": {
        "text": "Same Players",
        "callback": function() {
          gquery("restart_game", {});
        }
      },
      "reveal_hand": {
        "text": "Reveal Hand",
        "callback": function() {
          gquery("reveal_hand", {});
        }
      }
    };
    for(var i = 0; i < btnIds.length; i++) {
      var x = centerX() + buttonWidth * (i-btnIds.length/2);
      var y =  mainTextHeight + 50;
      var id = btnIds[i];
      if(id == "empty") {
        continue;
      }
      var data = btns[id];
      var btn = new Button(id, x, y, buttonWidth-10, 40,
        data.text, false, data.callback);
      btn.render();
      buttons.push(btn);
    }
  }

  function mainText(text) {
    drawText(text, "main", centerX(), mainTextHeight);
  }

  function subText(text) {
    drawText(text, "sub", centerX(), mainTextHeight+30);
  }

  function scaleTile(width) {
    return width/179*240;
  }

  function drawText(text, type, x, y, width, height) {
    ctx.fillStyle = "#000";
    var tileFont = '"Chelsea"';
    var mainFont = '"NotoSans"';
    var center = false;
    var font = "8px {mainFont}";
    if(type == "supermain") {
      font = "40px {mainFont}";
      ctx.textAlign = "center";
    } else if(type == "main") {
      font = "30px {mainFont}";
      ctx.textAlign = "center";
    } else if(type == "sub") {
      font = "20px {mainFont}";
      ctx.textAlign = "center";
    } else if(type == "bold_sub") {
      font = "bold 20px {mainFont}";
      ctx.textAlign = "center";
    } else if(type == "heading") {
      font = "bold 16px {mainFont}";
      ctx.textAlign = "left";
    } else if(type == "name") {
      font = "15px {mainFont}";
      ctx.textAlign = "left";
    } else if(type == "log") {
      font = "15px {mainFont}";
      ctx.textAlign = "left";
    } else if(type == "bold_name") {
      font = "bold 15px {mainFont}";
      ctx.textAlign = "left";
    } else if(type == "button") {
      font = "20px {mainFont}";
      ctx.textAlign = "left";
      center = true;
    } else if(type == "small_button") {
      font = "15px {mainFont}";
      ctx.textAlign = "left";
      center = true;
    } else if(type == "tile") {
      font = "15px {mainFont}";
      ctx.textAlign = "left";
    } else if(type == "small_tile") {
      font = "{hei}px {tileFont}";
      ctx.textAlign = "left";
      ctx.fillStyle = 'rgba(30,30,30,1.0)';
      center = true;
    } else if(type == "small_red") {
      font = "{hei}px {tileFont}";
      ctx.textAlign = "left";
      ctx.fillStyle = 'rgba(180,0,0,1.0)';
      center = true;
    } else if(type == "small_green") {
      font = "{hei}px {tileFont}";
      ctx.textAlign = "left";
      ctx.fillStyle = 'rgba(0,127,0,1.0)';
      center = true;
    } else if(type == "small_blue") {
      font = "{hei}px {tileFont}";
      ctx.textAlign = "left";
      ctx.fillStyle = 'rgba(0,0,127,1.0)';
      center = true;
    } else {
      font = "8px {mainFont}";
    }
    ctx.font = font.replace("{mainFont}", mainFont)
                   .replace("{tileFont}", tileFont)
                   .replace("{hei}", height*0.8);
    if(center) {
      x -= ctx.measureText(text).width*0.5;
    }
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

  function insertList(lst, tile, pos) {
    var res = [];
    for(var i = 0; i <= lst.length; i++) {
      if(i == pos) {
        res.push(tile);
      }
      if(i < lst.length && lst[i] != tile) {
        res.push(lst[i]);
      }
    }
    return res;
  }

  function insertTile(drag_tile, pos) {
    that.state.hand = insertList(that.state.hand, drag_tile, pos);
    that.state.offered = removeTile(that.state.offered, drag_tile);
    gquery("rearrange_tiles", {"tiles": sendTiles(that.state.hand)});
  }

  function offerTile(drag_tile, pos, insert) {
    var off = that.state.offered;
    if(insert) {
      that.state.offered = insertList(off, drag_tile, pos);
    } else {
      var res = [];
      for(var i = 0; i <= off.length; i++) {
        if(pos == i) {
          res.push(drag_tile);
        } else if(i < off.length && off[i] != drag_tile) {
          res.push(off[i]);
        }
      }
      that.state.offered = res;
    }
    that.state.hand = removeTile(that.state.hand, drag_tile);

    gquery("offer_tiles", {"tiles": sendTiles(that.state.offered)});
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
    var isAction = (endpoint != "game_state");
    if(isAction) {
      actionTime = now();
    }
    data["game_id"] = game_id;
    data["player_id"] = player_id;
    query(endpoint, data, function(data) {
      if(isAction) {
        actionTime = null;
      }
      that.recvState(data);
    });
  }

  this.recvState = function(data) {

    firstLoad = false;
    if(data.error) {
      console.log(data.error);
      if(data.error != "Invalid player id" && data.error != "Invalid game id") {
        that.error = data.error;
        that.errorTime = now();
      }
    } else {
      // temporarily suppress updates
      if(actionTime !== null && (now()-actionTime) < actionDuration) {
        return;
      }
      that.state = data;
    }
  }

  this.mousedown = function(x,y) {
    mx = x;
    my = y;
    for(var i = 0; i < tiles.length; i++) {
      if(tiles[i].contains(x,y) && tiles[i].draggable) {
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
    mx = x;
    my = y;
    if (drag_tile_obj) {
      var xx = drag_tile_obj.centerX();
      var yy = drag_tile_obj.centerY();
      for (var i = 0; i < drop_targets.length; i++) {
        if (drop_targets[i].contains(xx,yy)) {
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
    if(kv[0] == "g") {
      game_id = kv[1];
    } else if (kv[0] == "player_id") {
      player_id = kv[1];
    }
  }

  if (player_id == null) {
    player_id = localStorage.getItem("player_id");
  }
  if (!player_id) {
    player_id = makeid(16);
    localStorage.setItem("player_id", player_id);
  }

  var game = new Game(game_id, player_id);

  // debug
  window.game = game;

	setInterval(function(){game.render()}, 30);
	setInterval(function(){game.loadState()}, 1000);
	setInterval(function(){game.rescale()}, 500);
}
