#!/usr/bin/env python3
"""
Gemini URL Search Tool - Main Entry Point

This is the main entry point for the Streamlit application.
Run with: streamlit run main.py
"""

import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Load environment variables
load_dotenv()

def setup_logging():
    """Setup logging configuration"""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        log_config = config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/app.log")
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
    except Exception as e:
        # Fallback logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logging.error(f"Failed to setup logging from config: {e}")

def validate_environment():
    """Validate required environment variables and files"""
    required_env_vars = ["GEMINI_API_KEY"]
    missing_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logging.error(f"Missing required environment variables: {missing_vars}")
        logging.error("Please copy .env.example to .env and set the required values")
        return False
    
    # Check if config.json exists
    if not os.path.exists("config.json"):
        logging.error("config.json not found")
        return False
    
    return True

def create_directories():
    """Create necessary directories"""
    directories = ["data", "logs", "data/cache"]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logging.info(f"Created directory: {directory}")

def main():
    """Main application entry point"""
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Gemini URL Search Tool")
    
    # Validate environment
    if not validate_environment():
        logger.error("Environment validation failed. Exiting.")
        sys.exit(1)
    
    # Create necessary directories
    create_directories()
    
    # Import and run the Streamlit app
    try:
        from ui.search_app import run_app
        logger.info("Launching Streamlit application")
        run_app()
        
    except ImportError as e:
        logger.error(f"Failed to import application modules: {e}")
        logger.error("Please ensure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()