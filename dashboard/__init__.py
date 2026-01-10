from flask import Flask
import os

def create_app():
    # Get the parent directory (project root)
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # Create Flask app with correct template and static folders
    app = Flask(__name__,
                template_folder=os.path.join(basedir, 'templates'),
                static_folder=os.path.join(basedir, 'static'))

    from dashboard import routes
    app.register_blueprint(routes.bp)

    return app
