from flask import Blueprint, render_template
from dashboard.data_loader import load_parkrun_data, get_athlete_info
from dashboard.charts import create_results_chart

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # Load ParkRun data
    df = load_parkrun_data()

    # Get athlete information
    athlete_info = get_athlete_info(df)

    # Create chart
    chart_html = create_results_chart(df)

    return render_template('index.html',
                          athlete_name=athlete_info['name'],
                          athlete_id=athlete_info['id'],
                          chart_html=chart_html)
