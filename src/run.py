import os

from app import create_app

app = create_app()

if __name__ == '__main__':
    debug = os.environ.get('PERFORMANCELENS_DEBUG', 'true').lower() in ('1', 'true', 'yes')
    host = os.environ.get('PERFORMANCELENS_HOST', '127.0.0.1')
    port = int(os.environ.get('PERFORMANCELENS_PORT', '5000'))
    app.run(debug=debug, host=host, port=port)