from flask import Flask
from threading import Thread
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)  # Use __name__ for Flask app instantiation

@app.route('/')
def home():
    """
    A simple endpoint to indicate that the web server is running.
    This is often used by uptime monitoring services.
    """
    logging.info("Keep-alive endpoint '/' was accessed.")
    return "I'm alive"

def _run_flask_app():
    """
    Runs the Flask web server.
    This function is intended to be run in a separate thread.
    It's made private by convention (leading underscore) as it's an internal part of keep_alive.
    """
    try:
        # Consider using a more production-ready WSGI server like gunicorn or waitress
        # if this were a more complex application, but for a simple keep-alive, Flask's
        # development server is often sufficient.
        logging.info("Starting Flask keep-alive server on host 0.0.0.0, port 8080.")
        app.run(host='0.0.0.0', port=8080)
    except Exception as e:
        logging.error(f"Flask keep-alive server failed: {e}", exc_info=True)

def keep_alive():
    """
    Starts the Flask web server in a new daemon thread.
    Daemon threads automatically exit when the main program exits.
    """
    logging.info("Initializing keep-alive thread.")
    keep_alive_thread = Thread(target=_run_flask_app, name="KeepAliveThread")
    keep_alive_thread.daemon = True  # Set as a daemon thread
    keep_alive_thread.start()
    logging.info("Keep-alive thread started.")

if __name__ == '__main__':
    # This block allows running the Flask app directly for testing,
    # though it's typically started via the keep_alive() function from another module.
    logging.info("Running keep_alive.py directly for testing.")
    keep_alive()
    # Keep the main thread alive if running directly, otherwise it might exit too soon
    # In a real bot, the bot's main loop would keep the program running.
    import time
    try:
        while True:
            time.sleep(60)
            logging.info("Main thread still alive (keep_alive.py direct run test)")
    except KeyboardInterrupt:
        logging.info("keep_alive.py direct run test stopped.")