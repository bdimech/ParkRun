from flask import Blueprint, render_template, request
from dashboard.data_loader import load_parkrun_data, get_athlete_info
from dashboard.charts import create_results_chart

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # Check if auto-update should be disabled (e.g., ?no_update=1)
    no_update = request.args.get('no_update', '0') == '1'
    auto_update = not no_update

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
