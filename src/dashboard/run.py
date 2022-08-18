#!/usr/bin/env python
from dash import html, dcc, Dash, Input, Output
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
    '''
    pred_dir = "data/predictions/"
    pred_files = list(os.scandir(pred_dir))
    pred_files.sort(key=lambda f: f.name)

    df = pd.read_csv(pred_files.pop().path, index_col=0)

    # Add color column for predictions > THRESHOLD
    df["color"] = df.ChurnProb.apply(
        lambda x: "Convert" if x < THRESHOLD else "Churn")

    return df

new_trialers = load_data()
app = JupyterDash(__name__)
server = app.server

def make_figure_1():
    return px.scatter(
        new_trialers, 
        x='ChurnProb', 
        y="total_watchtime_day_1",
        facet_row='trial_length_days',
        labels={"trial_length_days": "Length of Trial",
                "total_watchtime_day_1": "Video watch time day 1", 
                "ChurnProb": "Probability of Churning"},
        color_discrete_sequence=["green", "red"],
        color='color')

@app.callback(
    Output('table-1', 'children'),
    Input('graph-1', 'hoverData'))
def make_table_1(value):
    '''
    Construct HTML table from non-zero data in row selected by hovering
    '''
    if value:
        index = value['points'][0]['pointNumber']
        series = new_trialers.iloc[index]
        index = series.index.values.tolist()
        return html.Table(
            [
                html.Thead(
                    html.Tr([html.Th("Item"), html.Th("Value")])
                ),
                html.Tbody([
                    html.Tr([
                        html.Td(ind),
                        html.Td(series.loc[ind]),
                    ]) for ind in index if series.loc[ind] != 0
                ])
            ]
        )
    else:
        return None

app.layout = html.Div([
    html.H1(
        'Skillshare Churn Predictions',
        style={
            'textAlign': 'center',
            'color': 'black',
            "background": "white"}),
    html.P("\n\n"),
    html.Div([
        dcc.Graph(
            id='graph-1',
            figure=make_figure_1()),
        html.Table(
            id='table-1',
            style={
                "margin-left": "auto",
                "margin-right": "auto"}
        )],
        style={
            "margin": "0% 25% 0% 25%"
        })])

app.run_server(debug=True)
