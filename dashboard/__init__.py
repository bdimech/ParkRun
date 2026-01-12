from flask import Flask
import os

def create_app(auto_update=False):
    """
    Create and configure the Flask application.

    Args:
        auto_update: If True, fetch fresh data from ParkRun on startup
    """
    # Get the parent directory (project root)
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # Create Flask app with correct template and static folders
    app = Flask(__name__,
                template_folder=os.path.join(basedir, 'templates'),
                static_folder=os.path.join(basedir, 'static'))

    # Perform web scraping once at startup if requested
    if auto_update:
        from dashboard.data_loader import update_results_from_web
        import logging
        logger = logging.getLogger(__name__)

        logger.info("Fetching fresh data from ParkRun website...")
        results_path = os.path.join(basedir, 'data', 'results.csv')
        athletes_path = os.path.join(basedir, 'data', 'athletes.csv')

        try:
            update_results_from_web(results_path, athletes_path)
            logger.info("Data update completed successfully")
        except Exception as e:
            logger.error(f"Failed to update from web: {e}")
            logger.info("Continuing with cached data")

    from dashboard import routes
    app.register_blueprint(routes.bp)

    return app
