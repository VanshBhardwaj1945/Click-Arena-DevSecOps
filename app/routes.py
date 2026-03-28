from flask import render_template
from app.state import players, targets

def register_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/health')
    def health():
        return {'status': 'ok', 'players': len(players), 'targets': len(targets)}

    @app.route('/stats')
    def stats():
        from app.state import players, messages
        return {
            "active_players": len(players),
            "messages_sent": len(messages),
            "status": "live"
        }