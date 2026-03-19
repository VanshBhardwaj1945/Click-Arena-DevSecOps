from flask import request
from flask_socketio import emit
from datetime import datetime
from app.state import players, targets, messages
import random
import time
import threading

def make_target():
    return {
        'id': random.randint(1000, 9999),
        'x': random.randint(5, 90),
        'y': random.randint(10, 85),
    }

def target_spawner(socketio):
    while True:
        if len(targets) < 3:
            t = make_target()
            targets.append(t)
            socketio.emit('target_added', t)
        time.sleep(1.5)

def register_events(socketio):

    @socketio.on('connect')
    def on_connect():
        players[request.sid] = {'name': 'Anonymous', 'score': 0}
        emit('your_id', {'id': request.sid})
        emit('current_targets', targets)
        emit('chat_history', messages)
        socketio.emit('scores_update', {'players': players})

    @socketio.on('join')
    def on_join(data):
        name = data.get('name', 'Anonymous').strip() or 'Anonymous'
        players[request.sid]['name'] = name
        socketio.emit('scores_update', {'players': players})
        msg = {'system': True, 'text': f'{name} joined the game'}
        messages.append(msg)
        if len(messages) > 20:
            messages.pop(0)
        socketio.emit('new_message', msg)

    @socketio.on('chat_message')
    def on_chat(data):
        text = data.get('text', '').strip()
        if not text or len(text) > 120:
            return
        name = players.get(request.sid, {}).get('name', 'Anonymous')
        msg = {
            'system': False,
            'name': name,
            'text': text,
            'time': datetime.now().strftime('%H:%M')
        }
        messages.append(msg)
        if len(messages) > 20:
            messages.pop(0)
        socketio.emit('new_message', msg)

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
        name = players.get(request.sid, {}).get('name', 'Anonymous')
        players.pop(request.sid, None)
        msg = {'system': True, 'text': f'{name} left the game'}
        messages.append(msg)
        if len(messages) > 20:
            messages.pop(0)
        socketio.emit('new_message', msg)
        socketio.emit('scores_update', {'players': players})