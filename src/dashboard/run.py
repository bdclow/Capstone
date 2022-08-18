#!/usr/bin/env python
from dash import html, dcc, Dash, Input, Output, dash_table
from jupyter_dash import JupyterDash
import plotly.express as px
import pandas as pd
import os

# Threshold for whether likely to conver or churn
THRESHOLD = 0.65

# If no files present, need to run pipeline for predictions (e.g. 'make all' or 'make sample')
def load_data() -> pd.DataFrame:
    '''
    Gets most recent set of predictions
    Loads into pandas DataFrame
    Cleans up columns (e.g. one hot cols, extraneous, etc)
    '''
    pred_dir = "data/predictions/"
    pred_files = list(os.scandir(pred_dir))
    pred_files.sort(key=lambda f: f.name)


    df = pd.read_csv(pred_files.pop().path, index_col=0)

    # UTM Campaign
    utm = df[df.columns[2:18]]
    # Video categories
    categories = df[df.columns[31:70]]
    watched_length_cols = [col for col in df.columns if "watched_video_length" in col]

    cols_to_drop = list(utm.columns)
    cols_to_drop.extend(["Prediction", "success"])
    cols_to_drop.extend(categories.columns)
    cols_to_drop.extend(watched_length_cols)

    # Add color column for predictions > THRESHOLD
    df["Predicted"] = df.ChurnProb.apply(
        lambda x: "Convert" if x < THRESHOLD else "Churn")

    df.ChurnProb = df.ChurnProb.round(2)

    df = df.drop(columns=cols_to_drop)
    df["UTM Campaign"] = utm.idxmax(1)

    # Clean up column names
    df = df.rename(columns={
        col: col.replace("_", " ").title() 
        for col in df.columns})

    return df

new_trialers = load_data()
app = JupyterDash(__name__)
server = app.server

def make_figure_1():
    return px.scatter(
        new_trialers, 
        x='Churnprob', 
        y="Total Watchtime Day 1",
        facet_row='Trial Length Days',
        labels={"trial_length_days": "Length of Trial",
                "total_watchtime_day_1": "Video watch time day 1", 
                "Churnprob": "Probability of Churning"},
        color_discrete_sequence=["green", "red"],
        color='Predicted')

@app.callback(
    Output('table-1', 'active_cell'),
    Input('graph-1', 'hoverData'))
def highlight_table_1(value):
    if value:
        index = value['points'][0]['pointNumber']
        return {'row': index, 'column': 0}
    return None

app.layout = html.Div(
    [
        html.H1(
            'Skillshare P1 Conversion Predictions',
            style={
                'textAlign': 'center',
                'color': 'black',
                "background": "white"}
        ),
        html.P("\n\n", id="lb"),
        html.Div(
            [
                dcc.Graph(
                    id='graph-1',
                    figure=make_figure_1()
                ),
            ],
            style={
                "margin": "0% 25% 0% 25%"
            }
        ),
        dash_table.DataTable(
            new_trialers.to_dict('records'), 
            [{"name": i, "id": i} for i in new_trialers.columns],
            id='table-1'
        )
    ]
)

app.run_server(debug=True)
