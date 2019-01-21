#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  8 17:02:44 2018

@author: lindseyb
"""

import base64
import io

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html

import pandas as pd
from scipy import optimize
import numpy as np


def piecewise_linear(x, x0, y0, k1, k2):
    return np.piecewise(x, [x < x0], [lambda x:k1*x + y0-k1*x0, lambda x:k2*x + y0-k2*x0])
    
def make_annotation_item(x, y, p, cn):
    return dict(xref='x', yref='y',
                x=x, y=y,
                font=dict(color='rgb(98,196,98)'),
                xanchor='left',
                yanchor='middle',
                text= "{}: {}, {}: {}".format(cn[0], round(p[0],1), cn[1], round(p[1],1)),
                showarrow=False)

app = dash.Dash(__name__)
colors = {
    'background': '#272B30',
    'text': '#aaa'
}
app.layout = html.Div([
    html.H1(children='Inflection Detection - single'),
    html.Div(children='''
        Detects a single data inflection in x,y data using least-squares piecewise regression 
    '''),
    html.Div(children='''
        Upload a single data file (.xls, .xlsx or .csv) with two columns of x-y data, with column names in the first row
    '''),         
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    html.Div(id='output-data-upload'),
])


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    df=df.dropna()
    cn = df.columns
    x = np.array(df.ix[:,0])
    y = np.array(df.ix[:,1])
    p0 = [np.nanmean(x), np.nanmean(y), 1, 1]
    p , e = optimize.curve_fit(piecewise_linear, x, y, p0)  # set initial parameter estimates
    xd = np.linspace(np.min(x), np.max(x), len(x))
    yd = piecewise_linear(xd, *p)
    ANNOTATIONS = [make_annotation_item(x=p[0]*.75, y=np.max(y)*1.1, p=p, cn=cn)]
    return html.Div([
        html.Hr(),  # horizontal line
        html.Div([
                dcc.Graph(
                   id = 'data-trace',
                   figure={
                            'data':[
                                    {'x': x, 'y': y,
                                     'type': 'scatter', 'name' : 'Data',
                                     'mode':'markers'},
                                     {'x': xd, 'y': yd, 'name' : 'Regression'}
                                ],
                               'layout': {
                                    'autosize':'False',
                                    'height':'340',
                                    'hovermode':'closest',
                                    'margin':{
                                      "r": '40',
                                      "t": '40',
                                      "b": '60',
                                      "l": '60'
                                     },
                                    'showlegend': 'False',
                                    'title':"",
                                    'width':'750',
                                    'xaxis':{'title':cn[0]},
                                    'yaxis':{'title':cn[1]},
                                    'annotations': ANNOTATIONS,
                                    'plot_bgcolor':colors['background'],
                                    'paper_bgcolor':colors['background'],
                                    'font':{'color': colors['text']},
                                    'shapes':[
                                        {'x0':p[0], 'y0':np.max(y),
                                         'x1':p[0], 'y1':0,
                                         'line':{'width':2,
                                                 'dash': 'dashdot',
                                                 'color':'rgb(98,196,98)'},
                                                }
                                        ]
                                           }      
                                    },
                    config={
                        'displayModeBar': False
                    } 
       
                )
            ], className="six columns"),
    html.Br(),
    html.Br(),
    html.Div(children='Created by: LM Boulet'),
    html.Div(children='Email: lindseyboulet@gmail.com')
    ])


@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children

if __name__ == '__main__':
    app.run_server(debug=True)
