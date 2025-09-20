import logging
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# from flask_session import Session

# Load environment variables
load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__)

    # Configuration
    if test_config is None:
        app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
        app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    else:
        app.config.update(test_config)

    # Use built-in Flask sessions instead of flask-session
    # This avoids the bytes/string type error with flask-session library

    # Setup logging
    if not app.debug:
        logging.basicConfig(level=logging.INFO)

    # Initialize rate limiting
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=os.getenv("REDIS_URL", "memory://"),
        storage_options={"socket_connect_timeout": 30},
        strategy="fixed-window",
    )

    # Register blueprints
    from src.routes.api import api_bp
    from src.routes.auth import auth_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    # Apply rate limiting to API endpoints
    limiter.limit("30 per minute")(api_bp)
    limiter.limit("10 per minute")(auth_bp)

    # Health check endpoint (exempt from rate limiting)
    @app.route("/health")
    @limiter.exempt
    def health_check():
        from src.utils.cache import cache_health_check

        cache_status = cache_health_check()
        return jsonify(
            {"status": "healthy", "service": "Song Soulmate", "cache": cache_status}
        )

    # Cache status endpoint
    @app.route("/cache/status")
    @limiter.limit("5 per minute")
    def cache_status():
        from src.utils.cache import cache_manager

        return jsonify(cache_manager.get_cache_info())

    # Main route
    @app.route("/")
    def index():
        return render_template("index.html")

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return (
            jsonify(
                {
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": error.retry_after,
                }
            ),
            429,
        )

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"])
