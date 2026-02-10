"""
Module for creating Plotly charts
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def format_seconds_to_mmss(seconds):
    """Convert seconds to MM:SS format for axis labels"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


def create_results_chart(df):
    """
    Create an interactive scatter plot of ParkRun results.

    Args:
        df: DataFrame with columns: Event, Date, TimeSeconds, TimeFormatted,
            Position, AgeGrade, IsPB

    Returns:
        str: HTML div containing the Plotly chart
    """
    fig = go.Figure()

    # Sort by date to identify PBs chronologically
    df_sorted = df.sort_values('Date').reset_index(drop=True)

    # Identify all PBs (times faster than all previous times)
    pb_indices = []
    min_time_so_far = float('inf')
    for idx, row in df_sorted.iterrows():
        if row['TimeSeconds'] < min_time_so_far:
            pb_indices.append(idx)
            min_time_so_far = row['TimeSeconds']

    # Mark PBs in the sorted dataframe
    df_sorted['IsPB'] = False
    df_sorted.loc[pb_indices, 'IsPB'] = True

    # Get events ordered by race count (highest first)
    event_counts = df_sorted['Event'].value_counts()
    events = event_counts.index.tolist()

    # Color palette for different events
    colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]

    # Create event to color mapping
    event_colors = {event: colors[i % len(colors)] for i, event in enumerate(events)}

    # First pass: Add all results as colored dots
    for i, event in enumerate(events):
        event_df = df_sorted[df_sorted['Event'] == event]
        color = event_colors[event]
        race_count = len(event_df)

        # Add all points as circles (show in legend)
        fig.add_trace(go.Scatter(
            x=event_df['Date'],
            y=event_df['TimeSeconds'],
            mode='markers',
            name=f"{event} ({race_count})",
            marker=dict(
                size=8,
                color=color,
                symbol='circle',
                line=dict(width=1, color='white')
            ),
            customdata=event_df[['TimeFormatted', 'Position', 'AgeGrade']],
            hovertemplate=(
                '<b>%{fullData.name}</b><br>' +
                'Date: %{x|%d/%m/%Y}<br>' +
                'Time: %{customdata[0]}<br>' +
                'Position: %{customdata[1]}<br>' +
                'Age Grade: %{customdata[2]}<br>' +
                '<extra></extra>'
            ),
            legendgroup=event,
            showlegend=True
        ))

    # Second pass: Add PB overlay stars (hidden by default, not in legend)
    for i, event in enumerate(events):
        event_df = df_sorted[df_sorted['Event'] == event]
        color = event_colors[event]
        pb_df = event_df[event_df['IsPB']]

        if not pb_df.empty:
            fig.add_trace(go.Scatter(
                x=pb_df['Date'],
                y=pb_df['TimeSeconds'],
                mode='markers',
                name=f"{event} PB",
                marker=dict(
                    size=14,
                    color=color,
                    symbol='star',
                    line=dict(width=2, color='gold')
                ),
                legendgroup=event,
                showlegend=False,
                visible=False,  # Hidden by default
                hoverinfo='skip'  # Don't show hover on PB stars
            ))

    # Calculate dynamic axis ranges based on data
    # X-axis: dates with padding
    x_min = df['Date'].min() - pd.DateOffset(months=1)
    x_max = df['Date'].max() + pd.DateOffset(months=1)

    # Y-axis: times with padding
    y_data_min = df['TimeSeconds'].min()
    y_data_max = df['TimeSeconds'].max()

    # Add padding to y-axis (round down to nearest minute for min, up for max)
    tick_interval = 60  # 1 minute intervals
    y_min = int(y_data_min // tick_interval) * tick_interval - tick_interval
    y_max = int(y_data_max // tick_interval + 1) * tick_interval + tick_interval

    # Create tick values and labels for y-axis
    y_ticks = list(range(y_min, y_max + tick_interval, tick_interval))
    y_tick_labels = [format_seconds_to_mmss(t) for t in y_ticks]

    # Add monthly dotted vertical lines - cover full Golden Zone range for toggle
    shapes = []
    # Start from earliest possible date (Golden Zone start)
    golden_start = pd.Timestamp('2022-01-01')
    golden_end = pd.Timestamp('2026-06-30')
    current_date = golden_start
    while current_date <= golden_end:
        shapes.append(dict(
            type='line',
            x0=current_date,
            x1=current_date,
            y0=0,
            y1=1,
            yref='paper',
            line=dict(color='lightgray', width=1, dash='dot')
        ))
        current_date += pd.DateOffset(months=1)

    # Calculate visibility arrays for PB toggle
    # Location traces (circles) are always visible
    num_events = len(events)
    # Total traces = location circles + PB stars
    total_traces = len(fig.data)

    # Visibility when PBs are shown (all traces visible)
    pb_show_visible = [True] * total_traces

    # Visibility when PBs are hidden (only location traces visible)
    pb_hide_visible = [True] * num_events + [False] * (total_traces - num_events)

    # Update layout
    fig.update_layout(
        title=dict(
            text='ParkRun Results Over Time',
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title='Date',
            showgrid=True,
            gridcolor='lightgray',
            showline=True,
            linewidth=2,
            linecolor='black',
            mirror=True,
            range=[x_min, x_max],
            fixedrange=True,
            tickangle=-45,
            tickfont=dict(size=10),
            title_standoff=25
        ),
        yaxis=dict(
            title='Time',
            showgrid=True,
            gridcolor='lightgray',
            tickmode='array',
            tickvals=y_ticks,
            ticktext=y_tick_labels,
            showline=True,
            linewidth=2,
            linecolor='black',
            mirror=True,
            range=[y_min, y_max],
            fixedrange=True,
            tickfont=dict(size=10),
            title_standoff=15
        ),
        hovermode='closest',
        plot_bgcolor='white',
        height=600,
        margin=dict(l=80, b=100, r=250, t=60),
        legend=dict(
            yanchor='top',
            y=0.95,
            xanchor='left',
            x=1.02,
            bordercolor='black',
            borderwidth=2,
            bgcolor='white',
            font=dict(size=11),
            itemsizing='constant',
            tracegroupgap=8
        ),
        updatemenus=[
            # View toggle (All Results / Golden Zone)
            dict(
                type='buttons',
                direction='down',
                active=0,  # Highlight "All Results" by default
                x=1.02,
                y=0.20,
                xanchor='left',
                yanchor='top',
                buttons=[
                    dict(
                        label='All Results',
                        method='relayout',
                        args=[{'xaxis.range': [x_min, x_max],
                               'yaxis.range': [y_min, y_max]}]
                    ),
                    dict(
                        label='Golden Zone',
                        method='relayout',
                        args=[{'xaxis.range': ['2022-01-01', '2026-06-30'],
                               'yaxis.range': [20*60, 30*60]}]
                    )
                ],
                bgcolor='lightgray',
                bordercolor='black',
                borderwidth=1
            ),
            # PB toggle (Show / Hide)
            dict(
                type='buttons',
                direction='down',
                active=0,  # Highlight "Hide PBs" by default
                x=1.02,
                y=-0.05,
                xanchor='left',
                yanchor='top',
                buttons=[
                    dict(
                        label='Hide PBs',
                        method='update',
                        args=[{'visible': pb_hide_visible}]
                    ),
                    dict(
                        label='Show PBs',
                        method='update',
                        args=[{'visible': pb_show_visible}]
                    )
                ],
                bgcolor='lightgray',
                bordercolor='black',
                borderwidth=1
            )
        ],
        annotations=[
            dict(
                text='<b>Race Location (Count)</b>',
                x=1.02,
                y=1.0,
                xref='paper',
                yref='paper',
                xanchor='left',
                showarrow=False,
                font=dict(size=12)
            )
        ],
        shapes=shapes
    )

    # Convert to HTML
    return fig.to_html(full_html=False, include_plotlyjs='cdn')
