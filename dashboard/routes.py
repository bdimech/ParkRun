from flask import Blueprint, render_template, request, current_app
from dashboard.data_loader import load_parkrun_data, get_athlete_info
from dashboard.charts import create_results_chart

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # Default to command-line setting
    auto_update = current_app.config.get('AUTO_UPDATE', False)

    # Allow URL parameter to override (e.g., ?no_update=1 or ?update=1)
    if request.args.get('no_update') == '1':
        auto_update = False
    elif request.args.get('update') == '1':
        auto_update = True

    # Load ParkRun data (optionally fetching latest from web)
    df = load_parkrun_data(auto_update=auto_update)

    # Get athlete information
    athlete_info = get_athlete_info(df)

    # Create chart
    chart_html = create_results_chart(df)

    return render_template('index.html',
                          athlete_name=athlete_info['name'],
                          athlete_id=athlete_info['id'],
                          chart_html=chart_html)
