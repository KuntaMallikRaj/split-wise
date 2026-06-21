import os

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from config import Config
from extensions import db

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")


def create_app():
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)

    # Import models before create_all() so their tables are registered on the
    # metadata; otherwise create_all() creates nothing on a fresh database.
    import models  # noqa: F401

    with app.app_context():
        db.create_all()

    from routes.users import users_bp
    from routes.groups import groups_bp
    from routes.expenses import expenses_bp
    from routes.settlements import settlements_bp

    app.register_blueprint(users_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(settlements_bp)

    @app.route("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.route("/health")
    def health():
        return jsonify({"service": "Split-Wise", "status": "ok"}), 200

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "internal server error"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
