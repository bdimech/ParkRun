from flask import Blueprint, render_template, request, current_app
from dashboard.data_loader import load_parkrun_data, get_athlete_info, load_athletes_config
from dashboard.charts import create_results_chart

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # Load all athletes
    athletes_df = load_athletes_config()

    # Get selected athlete_id from URL parameter
    selected_athlete_id = request.args.get('athlete_id', type=str)

    # If no athlete selected, default to the first one
    if selected_athlete_id is None and not athletes_df.empty:
        selected_athlete_id = str(athletes_df.iloc[0]['parkrun_id'])

    # Load ParkRun data from cached CSV (web scraping happens at startup only)
    df = load_parkrun_data(auto_update=False)

    # Filter data for selected athlete if AthleteID column exists
    if 'AthleteID' in df.columns and selected_athlete_id:
        df = df[df['AthleteID'].astype(str) == selected_athlete_id]

    # Get athlete information
    athlete_info = get_athlete_info(df)

    # If we have a selected_athlete_id, use it to get the correct name from athletes_df
    if selected_athlete_id and not athletes_df.empty:
        athlete_row = athletes_df[athletes_df['parkrun_id'].astype(str) == selected_athlete_id]
        if not athlete_row.empty:
            athlete_info['name'] = athlete_row.iloc[0]['name']
            athlete_info['id'] = selected_athlete_id

    # Check if there are any results
    if df.empty:
        chart_html = '<div class="no-results">No results available for this athlete.</div>'
    else:
        # Create chart
        chart_html = create_results_chart(df)

    return render_template('index.html',
                          athlete_name=athlete_info['name'],
                          athlete_id=athlete_info['id'],
                          athletes=athletes_df.to_dict('records'),
                          selected_athlete_id=selected_athlete_id,
                          chart_html=chart_html)
