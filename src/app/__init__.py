import mimetypes
import os
from flask import Flask, session

# Force Flask to recognize .woff2 files correctly
mimetypes.add_type('font/woff2', '.woff2')
mimetypes.add_type('font/woff', '.woff')


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get(
        'PERFORMANCELENS_SECRET_KEY',
        'dev-insecure-change-for-packaged-build',
    )

    @app.context_processor
    def inject_user():
        name = (session.get('user_name') or '').strip()
        if not name:
            return {
                'user_display_name': 'Student',
                'user_initial': 'S',
            }
        return {
            'user_display_name': name,
            'user_initial': (name[0].upper() if name else 'S'),
        }

    from . import routes

    app.register_blueprint(routes.bp)
    routes.init_db()

    return app