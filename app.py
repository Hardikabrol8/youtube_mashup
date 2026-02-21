import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from config import Config
from routes import main_bp

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        RotatingFileHandler("logs/application.log", maxBytes=1024 * 1024 * 5, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_app():
    # Validate critical configuration
    config_errors = Config.validate_config()
    if config_errors:
        for err in config_errors:
            logger.warning(f"Configuration Warning: {err}")
    else:
        logger.info("Configuration validated successfully.")

    app = Flask(__name__)
    app.config.from_object(Config)

    # Register blueprints
    app.register_blueprint(main_bp)

    logger.info("Flask Application initialized successfully.")
    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
