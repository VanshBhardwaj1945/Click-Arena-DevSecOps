from flask import render_template
from app.state import players, targets

def register_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/health')
    def health():
        return {'status': 'ok', 'players': len(players), 'targets': len(targets)}