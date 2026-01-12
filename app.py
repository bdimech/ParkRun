import argparse
from dashboard import create_app

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='ParkRun Dashboard - Display your ParkRun results'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Fetch fresh data from ParkRun website before starting dashboard'
    )
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    app = create_app(auto_update=args.update)
    app.run(debug=True)
