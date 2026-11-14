import os
import warnings
warnings.filterwarnings("ignore", category=Warning)
from flask import Flask
from flask_cors import CORS
from config import Config
from backend.routes import api_bp, web_bp

def create_app():
    # Frontend directory paths
    template_dir = os.path.join(Config.BASE_DIR, 'frontend', 'templates')
    static_dir = os.path.join(Config.BASE_DIR, 'frontend', 'static')

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(Config)

    # Enable CORS for API consumers
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(web_bp)

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    host = os.environ.get('HOST', '0.0.0.0')
    print(f"[*] Starting Landslide Risk Mapper on http://{host}:{port}")
    app.run(host=host, port=port, debug=Config.DEBUG)
