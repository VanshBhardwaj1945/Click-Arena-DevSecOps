import os
from flask import Flask
from flask_socketio import SocketIO
import threading
from app.routes import register_routes
from app.game import register_events, target_spawner

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.config['SECRET_KEY'] = 'devsecops-weekend'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

register_routes(app)
register_events(socketio)

if __name__ == '__main__':
    threading.Thread(target=target_spawner, args=(socketio,), daemon=True).start()
    print("▶  Game running at http://localhost:8080")
    print("▶  Health check at http://localhost:8080/health")
    socketio.run(app, host='0.0.0.0', port=8080, debug=False, allow_unsafe_werkzeug=True)