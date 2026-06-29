## @file dashboard.py
#  @brief Interactive dashboard based on Plotly Dash to display results.
#  @details Loads and groups the CSV data collected by the evaluator, allowing easy visual 
#           inspection of estimated vs. real trajectories and generated error metrics.

import os
import glob
import pandas as pd
import dash
from dash import html, dcc, Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# === 1. SETUP AND DATA READING ===
base_results_dir = "/workspace/results"

search_paths = {
    "Standard": os.path.join(base_results_dir, "amcl", "*.csv"),
    "Dinamici": os.path.join(base_results_dir, "amcl_actors", "*.csv"),
    "Noise": os.path.join(base_results_dir, "amcl_noise", "*.csv"),
    "Extreme Noise": os.path.join(base_results_dir, "amcl_extr", "*.csv"),
    "Kidnapping": os.path.join(base_results_dir, "amcl_kidnapping", "*.csv")
}

all_runs_data = {}
category_means = []

print("🔍 Calculating averages per folder...")

for category, path_pattern in search_paths.items():
    cat_trans_errors = []
    cat_rot_errors = []
    
    for file_path in glob.glob(path_pattern):
        try:
            df = pd.read_csv(file_path)
            # Store full data for the dropdown
            run_label = f"{category} - {os.path.basename(file_path)}"
            all_runs_data[run_label] = df
            
            # Accumulate for category average
            cat_trans_errors.append(df["Error_Translation_m"].mean())
            cat_rot_errors.append(df["Error_Rotation_deg"].mean())
        except Exception as e:
            print(f"❌ Error in {file_path}: {e}")
            
    if cat_trans_errors:
        category_means.append({
            "Category": category,
            "Mean_Translation": sum(cat_trans_errors) / len(cat_trans_errors),
            "Mean_Rotation": sum(cat_rot_errors) / len(cat_rot_errors)
        })

# === 2. GROUPED BAR CHART (AVERAGES PER FOLDER) ===
means_df = pd.DataFrame(category_means)
fig_compare = go.Figure()

fig_compare.add_trace(go.Bar(
    x=means_df["Category"], y=means_df["Mean_Translation"],
    name="Mean Translation Error (m)", marker_color="#1f77b4"
))
fig_compare.add_trace(go.Bar(
    x=means_df["Category"], y=means_df["Mean_Rotation"],
    name="Mean Rotational Error (°)", marker_color="#2ca02c"
))

fig_compare.update_layout(
    title_text="📊 Error Averages Comparison by Scenario",
    barmode='group',
    xaxis_title="Scenario (Folder)",
    yaxis_title="Mean Value",
    template="plotly_white"
)

# === 3. DASH APP INITIALIZATION ===
app = dash.Dash(__name__)

# Application layout
app.layout = html.Div(children=[
    html.H1("🤖 G1 EDU: Robustness Evaluation Dashboard", style={'textAlign': 'center', 'font-family': 'Arial'}),
    html.P("Comparison between Standard Navigation, Dynamic Obstacles, and Kidnapping", style={'textAlign': 'center', 'font-family': 'Arial', 'color': '#555'}),
    
    # Summary Bar Chart
    html.Div(dcc.Graph(figure=fig_compare)),
    html.Hr(style={'margin': '30px 0', 'border': '1px solid #ddd'}),
    
    # Interactive Detail Section
    html.H2("🔍 Detailed Run Analysis", style={'textAlign': 'center', 'font-family': 'Arial'}),
    html.Div([
        html.Label("Select the test to display:", style={'font-family': 'Arial', 'fontWeight': 'bold'}),
        dcc.Dropdown(
            id='run-selector',
            options=[{'label': key, 'value': key} for key in all_runs_data.keys()],
            value=list(all_runs_data.keys())[0] if all_runs_data else None,
            clearable=False,
            style={'width': '60%', 'margin': '10px auto'}
        )
    ], style={'textAlign': 'center'}),
    
    # Trajectory Chart
    html.Div(dcc.Graph(id='trajectory-graph'), style={'display': 'flex', 'justify-content': 'center'}),
    
    # Error over time Chart
    dcc.Graph(id='error-graph')
])

# === 4. CALLBACK TO UPDATE CHARTS ON DROPDOWN CHANGE ===
@app.callback(
    [Output('trajectory-graph', 'figure'),
     Output('error-graph', 'figure')],
    [Input('run-selector', 'value')]
)
def update_graphs(selected_run):
    """!
    @brief Updates the interactive charts based on the file selected from the dropdown menu.
    
    @param selected_run String containing the test's identifier name.
    @return A tuple containing (Map Trajectory Figure, Error vs Time Figure).
    """
    if not selected_run or selected_run not in all_runs_data:
        return go.Figure(), go.Figure()
    
    df = all_runs_data[selected_run]
    
    # --- A. MAP CHART CONSTRUCTION (LIVE STYLE) ---
    fig_map = go.Figure()
    fig_map.add_trace(go.Scatter(
        x=df["GT_X"], y=df["GT_Y"], mode='lines', name="Real Path (Ground Truth)",
        line=dict(color="#1f77b4", width=2)
    ))
    fig_map.add_trace(go.Scatter(
        x=df["AMCL_X"], y=df["AMCL_Y"], mode='lines', name="Estimated Path (AMCL)",
        line=dict(color="#ff7f0e", width=2, dash="dash")
    ))

    # Error Lines (Shows the Kidnapping jump or drift)
    error_lines_x, error_lines_y = [], []
    step = max(1, len(df) // 100) 
    for i in range(0, len(df), step):
        row = df.iloc[i]
        if row["Error_Translation_m"] > 0.3: # Threshold at 0.3m
            error_lines_x.extend([row["GT_X"], row["AMCL_X"], None])
            error_lines_y.extend([row["GT_Y"], row["AMCL_Y"], None])

    if error_lines_x:
        fig_map.add_trace(go.Scatter(
            x=error_lines_x, y=error_lines_y, mode='lines', name="Error Vector (> 0.3m)",
            line=dict(color="red", width=1, dash="dot"), hoverinfo="skip", opacity=0.5
        ))

    fig_map.update_layout(
        title_text=f"Trajectory: {selected_run}",
        xaxis_title="X (m)", yaxis_title="Y (m)",
        width=700, height=700, plot_bgcolor="white",
        yaxis=dict(scaleanchor="x", scaleratio=1, showgrid=True, gridcolor="lightgray", zeroline=True, zerolinecolor="black", linecolor="black", mirror=True),
        xaxis=dict(showgrid=True, gridcolor="lightgray", zeroline=True, zerolinecolor="black", linecolor="black", mirror=True),
        hovermode="closest", legend=dict(orientation="h", yanchor="top", y=-0.10, xanchor="center", x=0.5)
    )

    # --- B. ERROR OVER TIME CHART CONSTRUCTION ---
    fig_error = make_subplots(specs=[[{"secondary_y": True}]])
    fig_error.add_trace(go.Scatter(
        x=df["Time_s"], y=df["Error_Translation_m"], name="Translational Error (m)", line=dict(color="red", width=2)
    ), secondary_y=False)
    fig_error.add_trace(go.Scatter(
        x=df["Time_s"], y=df["Error_Rotation_deg"], name="Rotational Error (°)", line=dict(color="purple", width=2, dash="dot")
    ), secondary_y=True)

    fig_error.update_layout(
        title_text=f"Error Trends: {selected_run}",
        xaxis_title="Time (s)", template="plotly_white", height=400, hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig_error.update_yaxes(title_text="Translation Error (m)", secondary_y=False, title_font=dict(color="red"))
    fig_error.update_yaxes(title_text="Rotation Error (Degrees)", secondary_y=True, title_font=dict(color="purple"))

    return fig_map, fig_error

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)