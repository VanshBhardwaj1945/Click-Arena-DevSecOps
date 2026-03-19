from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit
import random
import time
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'devsecops-weekend'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

players = {}
targets = []

def make_target():
    return {
        'id': random.randint(1000, 9999),
        'x': random.randint(5, 90),
        'y': random.randint(10, 85),
    }

def target_spawner():
    while True:
        if len(targets) < 3:
            t = make_target()
            targets.append(t)
            socketio.emit('target_added', t)
        time.sleep(1.5)

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Click Arena</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #1a1a2e; color: white; font-family: sans-serif; overflow: hidden; }
    #arena { position: relative; width: 100vw; height: 100vh; }
    #scoreboard {
      position: fixed; top: 14px; right: 14px;
      background: rgba(0,0,0,0.65); padding: 14px 20px;
      border-radius: 12px; min-width: 180px; z-index: 10;
    }
    #scoreboard h3 { font-size: 12px; opacity: 0.5; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
    .score-row { display: flex; justify-content: space-between; gap: 24px; font-size: 15px; margin: 5px 0; }
    .score-row.me { color: #e94560; font-weight: bold; }
    .target {
      position: absolute; width: 54px; height: 54px;
      background: #e94560; border-radius: 50%; cursor: pointer;
      transform: translate(-50%, -50%);
      display: flex; align-items: center; justify-content: center;
      font-size: 24px; box-shadow: 0 0 20px #e9456066;
      transition: transform 0.08s; user-select: none;
    }
    .target:hover  { transform: translate(-50%, -50%) scale(1.2); }
    .target:active { transform: translate(-50%, -50%) scale(0.9); }
    #join-screen {
      position: fixed; inset: 0; background: #1a1a2e;
      display: flex; flex-direction: column;
      align-items: center; justify-content: center; gap: 18px; z-index: 20;
    }
    #join-screen h1 { font-size: 3rem; letter-spacing: -1px; }
    #join-screen p  { opacity: 0.5; font-size: 15px; }
    #join-screen input {
      padding: 13px 22px; font-size: 17px; border-radius: 10px;
      border: 2px solid #e94560; background: #16213e;
      color: white; outline: none; text-align: center; width: 260px;
    }
    #join-screen input:focus { border-color: #ff6b81; }
    #join-screen button {
      padding: 13px 40px; font-size: 17px; border-radius: 10px;
      background: #e94560; color: white; border: none; cursor: pointer;
    }
    #join-screen button:hover { background: #ff6b81; }
    #player-count { position: fixed; top: 14px; left: 14px; font-size: 13px; opacity: 0.4; }
  </style>
</head>
<body>
  <div id="join-screen">
    <h1>Click Arena</h1>
    <p>Click the targets. Outscore everyone. Real-time multiplayer.</p>
    <input id="name-input" placeholder="Enter your name" maxlength="16" autocomplete="off"/>
    <button onclick="joinGame()">Play</button>
  </div>

  <div id="arena"></div>

  <div id="scoreboard">
    <h3>Leaderboard</h3>
    <div id="scores"></div>
  </div>

  <div id="player-count">0 players online</div>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.5/socket.io.min.js"></script>
  <script>
    const socket = io();
    const arena  = document.getElementById('arena');
    let myId     = null;

    document.getElementById('name-input').addEventListener('keydown', e => {
      if (e.key === 'Enter') joinGame();
    });

    function joinGame() {
      const name = document.getElementById('name-input').value.trim();
      if (!name) return;
      socket.emit('join', { name });
      document.getElementById('join-screen').style.display = 'none';
    }

    socket.on('your_id', (data) => { myId = data.id; });

    function drawTarget(t) {
      if (document.getElementById('t-' + t.id)) return;
      const el = document.createElement('div');
      el.className  = 'target';
      el.id         = 't-' + t.id;
      el.innerText  = '🎯';
      el.style.left = t.x + '%';
      el.style.top  = t.y + '%';
      el.addEventListener('click', () => {
        socket.emit('click_target', { id: t.id });
        el.style.pointerEvents = 'none';
      });
      arena.appendChild(el);
    }

    socket.on('target_added',   (t)    => drawTarget(t));
    socket.on('current_targets',(list) => list.forEach(t => drawTarget(t)));
    socket.on('target_removed', (data) => {
      const el = document.getElementById('t-' + data.id);
      if (el) el.remove();
    });

    socket.on('scores_update', (data) => {
      const sorted = Object.entries(data.players)
        .sort(([,a],[,b]) => b.score - a.score);
      document.getElementById('scores').innerHTML = sorted
        .map(([id, p]) => `
          <div class="score-row ${id === myId ? 'me' : ''}">
            <span>${p.name}${id === myId ? ' (you)' : ''}</span>
            <span>${p.score}</span>
          </div>`).join('');
      document.getElementById('player-count').textContent =
        sorted.length + ' player' + (sorted.length !== 1 ? 's' : '') + ' online';
    });
  </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/health')
def health():
    return {'status': 'ok', 'players': len(players), 'targets': len(targets)}

@socketio.on('connect')
def on_connect():
    players[request.sid] = {'name': 'Anonymous', 'score': 0}
    emit('your_id', {'id': request.sid})
    emit('current_targets', targets)
    socketio.emit('scores_update', {'players': players})

@socketio.on('join')
def on_join(data):
    name = data.get('name', 'Anonymous').strip() or 'Anonymous'
    players[request.sid]['name'] = name
    socketio.emit('scores_update', {'players': players})

@socketio.on('click_target')
def on_click(data):
    target_id = data.get('id')
    target = next((t for t in targets if t['id'] == target_id), None)
    if target:
        targets.remove(target)
        players[request.sid]['score'] += 1
        socketio.emit('target_removed', {'id': target_id})
        socketio.emit('scores_update', {'players': players})

@socketio.on('disconnect')
def on_disconnect():
    players.pop(request.sid, None)
    socketio.emit('scores_update', {'players': players})

if __name__ == '__main__':
    threading.Thread(target=target_spawner, daemon=True).start()
    print("▶  Game running at http://localhost:5000")
    print("▶  Health check at http://localhost:5000/health")
socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
