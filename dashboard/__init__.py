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

    # Store auto_update setting in Flask config
    app.config['AUTO_UPDATE'] = auto_update

    from dashboard import routes
    app.register_blueprint(routes.bp)

    return app
