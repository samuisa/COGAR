import os
import pandas as pd
import dash
from dash import html, dcc
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# === 1. Data loading and cleaning ===
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, "..", "results", "localization_results_kidnapping_failed.csv")

print(f"Looking for the file at: {csv_path}")

try:
    robot_df = pd.read_csv(csv_path, sep=",")
    robot_df.columns = [col.strip() for col in robot_df.columns]
    
    # Ensure data is numeric
    for col in ["Time_s", "Error_Translation_m", "Error_Rotation_deg", "GT_X", "GT_Y", "AMCL_X", "AMCL_Y"]:
        robot_df[col] = robot_df[col].astype(float)
    
    # === 2. Path Chart Creation (Turtle LIVE Style) ===
    fig_map = go.Figure()

    # Ground Truth Trace (Real Path)
    fig_map.add_trace(go.Scatter(
        x=robot_df["GT_X"], y=robot_df["GT_Y"],
        mode='lines',
        name="Real Path (Ground Truth)",
        line=dict(color="#1f77b4", width=2) # Classic Matplotlib blue
    ))

    # AMCL Trace (Estimated Path)
    fig_map.add_trace(go.Scatter(
        x=robot_df["AMCL_X"], y=robot_df["AMCL_Y"],
        mode='lines',
        name="Estimated Path (AMCL)",
        line=dict(color="#ff7f0e", width=2, dash="dash") # Classic Matplotlib orange
    ))

    # Temporal error segments (Kidnapping visualization)
    # error_lines_x = []
    # error_lines_y = []
    # step = max(1, len(robot_df) // 100) 
    
    # for i in range(0, len(robot_df), step):
    #     row = robot_df.iloc[i]
    #     if row["Error_Translation_m"] > 0.5:
    #         error_lines_x.extend([row["GT_X"], row["AMCL_X"], None])
    #         error_lines_y.extend([row["GT_Y"], row["AMCL_Y"], None])

    # fig_map.add_trace(go.Scatter(
    #     x=error_lines_x, y=error_lines_y,
    #     mode='lines',
    #     name="Error Vector (> 0.5m)",
    #     line=dict(color="red", width=1, dash="dot"),
    #     hoverinfo="skip",
    #     opacity=0.5
    # ))

    # TURTLE LIVE STYLE LAYOUT
    fig_map.update_layout(
        title_text="Robot LIVE Trajectory",
        xaxis_title="X",
        yaxis_title="Y",
        # Force a square/boxy shape just like Matplotlib's 'equal', 'box'
        width=700, 
        height=700,
        plot_bgcolor="white", # Clean white background
        yaxis=dict(
            scaleanchor="x", 
            scaleratio=1,
            showgrid=True,
            gridcolor="lightgray",
            zeroline=True,
            zerolinecolor="black",
            linecolor="black", # Box border
            mirror=True # Complete the box border
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="lightgray",
            zeroline=True,
            zerolinecolor="black",
            linecolor="black", # Box border
            mirror=True # Complete the box border
        ),
        hovermode="closest",
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5)
    )

    # === 3. Error Chart Creation (Dual Y-Axis) ===
    fig_error = make_subplots(specs=[[{"secondary_y": True}]])

    fig_error.add_trace(go.Scatter(
        x=robot_df["Time_s"], y=robot_df["Error_Translation_m"], 
        name="Translational Error (m)", line=dict(color="red", width=2)
    ), secondary_y=False)

    fig_error.add_trace(go.Scatter(
        x=robot_df["Time_s"], y=robot_df["Error_Rotation_deg"], 
        name="Rotational Error (°)", line=dict(color="purple", width=2, dash="dot")
    ), secondary_y=True)

    fig_error.update_layout(
        title_text="Error Trend Over Time",
        xaxis_title="Time (s)",
        template="plotly_white",
        height=400,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig_error.update_yaxes(title_text="Translation Error (m)", secondary_y=False, title_font=dict(color="red"))
    fig_error.update_yaxes(title_text="Rotation Error (Degrees)", secondary_y=True, title_font=dict(color="purple"))

    # === 4. Dash App Initialization ===
    app = dash.Dash(__name__)

    app.layout = html.Div(children=[
        html.H1("G1 EDU: Robustness Evaluation Dashboard", style={'textAlign': 'center', 'font-family': 'Arial'}),
        html.P("Live trajectory mimicking Matplotlib 'equal' aspect ratio.", style={'textAlign': 'center', 'font-family': 'Arial', 'color': '#555'}),
        
        # Center the boxy map chart
        html.Div(dcc.Graph(figure=fig_map), style={'display': 'flex', 'justify-content': 'center'}),
        html.Hr(style={'margin': '20px 0', 'border': '1px solid #eee'}),
        dcc.Graph(figure=fig_error)
    ])

    if __name__ == '__main__':
        app.run(debug=True, host='0.0.0.0', port=8050)

except FileNotFoundError:
    print("ERROR: CSV file not found. You must first run a test with the new benchmark_evaluator.py script to generate the data!")
except KeyError as e:
    print(f"ERROR: Missing column in CSV: {e}. Are you using an old CSV? Ensure you have generated a new test!")