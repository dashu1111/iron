from app import create_app
from waitress import serve
import os

app = create_app()
if __name__ == '__main__':
    os.makedirs(app.instance_path, exist_ok=True)
    serve(app, host='0.0.0.0', port=5000)