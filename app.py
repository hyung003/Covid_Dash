import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.express as px
import dash_auth
import pandas as pd

from config import getConnStr
from dash.dependencies import Output, Input


# Define Layout and Functions
def get_options(list):
    dict_list = []
    for i in list:
        dict_list.append({'label': i, 'value': i})

    return dict_list


def create_card(title, content, content2):
    card = dbc.Card(
        dbc.CardBody(
            [
                html.H4(title, className="card-title"),
                html.Br(),
                html.H2(content, className="card-subtitle"),
                html.H2(content2, className="card-subtitle"),
                html.Br()
            ]
        ),
        color="primary", inverse=False
    )
    return card


# Load data
query = """SELECT * FROM covid_data.covid_place_data  where date is not null and x is not null and x < 0 and 
confirmed_cases is not null """

query2 = """
SELECT 
date,
place,
sum(confirmed_cases) * 1.00 as total_cases
FROM covid_data.covid_place_data
where place in ( 'Westwood','Culver City','Irvine')
and date not in ('2020-07-03','2020-07-04','2020-07-05')
group by date, place
order by date desc limit 42;
"""

query3 = """
Select 
date, 
place,
round(case when place= 'Irvine' then (total_cases/282572.00) * 100000
	       when place = 'Westwood' then (total_cases/52102.00) * 100000
           when place = 'Culver City' then (total_cases/39214.00) * 100000
           else 0 end,3) as 'Total_cases_per_100k'
from (
SELECT 
date,
place,
sum(confirmed_cases) * 1.00 as total_cases
FROM covid_data.covid_place_data
where place in ( 'Westwood','Culver City','Irvine')
and date not in ('2020-07-03','2020-07-04','2020-07-05')
group by date, place) as myTable
order by date desc limit 42;
"""

# DataFrames
latimes = pd.read_sql_query(query, getConnStr())

df2 = pd.read_sql_query(query2, getConnStr())

df3 = pd.read_sql_query(query3, getConnStr())

# Total Values and Max Date
max_date = df2['date'][df2['date'] == df2['date'].max()].values[0]
irvine_total_cases = df2['total_cases'][(df2['place'] == 'Irvine') & (df2['date'] == max_date)].values[0]
westwood_total_cases = df2['total_cases'][(df2['place'] == 'Westwood') & (df2['date'] == max_date)].values[0]
culver_city_total_cases = df2['total_cases'][(df2['place'] == 'Culver City') & (df2['date'] == max_date)].values[0]

# latimes_today
latimes_today = latimes[(latimes['county'] == 'Los Angeles') & (latimes['date'] == max_date)]

# Total Values Per 100K
irvcasesper100 = df3['Total_cases_per_100k'][(df3['place'] == 'Irvine') & (df3['date'] == max_date)].values[0]
westcasesper100 = df3['Total_cases_per_100k'][(df3['place'] == 'Westwood') & (df3['date'] == max_date)].values[0]
culcasesper100 = df3['Total_cases_per_100k'][(df3['place'] == 'Culver City') & (df3['date'] == max_date)].values[0]

# Created Card
card3 = create_card("Number of Cases in Irvine", "{} Cases".format(irvine_total_cases),
                    "{} Cases per 100000 people".format(irvcasesper100))
card2 = create_card("Number of Cases in Culver City", "{} Cases".format(culver_city_total_cases),
                    "{} Cases per 100000 people".format(culcasesper100))
card1 = create_card("Number of Cases in Westwood", "{} Cases".format(westwood_total_cases),
                    "{} Cases per 100000 people".format(westcasesper100))

external_stylesheets = [
    '/Users/hyung/PycharmProjects/stats405_plotly_proj/assets/style.css'
]


app = dash.Dash(__name__,
                external_stylesheets=external_stylesheets)
#auth = dash_auth.BasicAuth(app, USERNAME_PASSWORD_PAIRS)
server = app.server

# Set Title
app.title = 'Covid Cases'

app.layout = html.Div(
    children=[
        dcc.Location(id='/app', pathname='/app', refresh=False),
        # Rows for cards on Dashboard
        html.Div([
            html.Div([
                dbc.Col(id='card1', children=[card1], md=3, style={"background-color": "rgb(0, 51, 171)"})
            ], className='four columns'
            ),
            html.Div([
                dbc.Col(id='card2', children=[card2], md=3,
                        style={"background-color": "teal"})
            ], className='four columns'
            ),
            html.Div([
                dbc.Col(id='card3', children=[card3], md=3,
                        style={"background-color": "purple"})
            ], className='four columns'
            ),
        ], className="row"
        ),
        html.Div(
            className='row',
            children=[
                # Column for user controls
                html.Div(
                    className='four columns',
                    children=[
                        html.H2('Covid Total Cases Per City'),
                        html.P('''
                        Visualizing Covid Cases for Westwood, Culver City and Irvine
                        '''
                               ),
                        html.P('''
                        Pick one or more cities from the dropdown below.
                        '''),
                        # Dropdown for stock selection
                        html.Div(
                            className='div-for-dropdown',
                            children=[
                                dcc.Dropdown(id='dropairlines', options=get_options(df2['place'].unique()),
                                             multi=True, value=df2['place'].unique(),
                                             placeholder="Select a City",
                                             style={'backgroundColor': '#1E1E1E'},
                                             className='stockselector'
                                             ),
                            ],
                            style={'color': '#1E1E1E'}),
                    ],
                ),
                html.Div([
                    html.Div([
                        dcc.Graph(id='histogram1')
                    ], className='four columns'
                    ),
                    html.Div([
                        dcc.Graph(id='histogram2'
                                  )
                    ], className='four columns'
                    ),

                ], className="row"
                ),
                html.Div([
                    html.Div([
                        html.Iframe(id='map1', srcDoc=open('Covid_data_big.html', 'r').read(), width='95%',
                                    height='600')
                    ], className='twelve columns'
                    ),
                ], className="row"
                ),
            ],
        )
    ]
)


@app.callback(
    Output('histogram1', 'figure'),
    [Input("dropairlines", "value")]
)
def update_figure(airline):
    df_sub = df2[df2.place.isin(airline)]
    return px.bar(df_sub,
                  x='date',
                  y='total_cases',
                  color='place',
                  template='plotly_dark',
                  color_discrete_map={
                      "Westwood": "rgb(0, 51, 171)",
                      "Culver City": "teal",
                      "Irvine": "purple"}
                  ).update_layout(
        {'title': {
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
            'plot_bgcolor': 'rgba(0, 0, 0, 0)',
            'paper_bgcolor': 'rgba(0, 0, 0, 0)'})


@app.callback(
    Output('histogram2', 'figure'),
    [Input("dropairlines", "value")]
)
def update_figure(value):
    df_sub = df3[df3.place.isin(value)]
    return px.bar(df_sub,
                  x='date',
                  y='Total_cases_per_100k',
                  color='place',
                  template='plotly_dark',
                  color_discrete_map={
                      "Westwood": "rgb(0, 51, 171)",
                      "Culver City": "teal",
                      "Irvine": "purple"}).update_layout(
        {'plot_bgcolor': 'rgba(0, 0, 0, 0)',
         'paper_bgcolor': 'rgba(0, 0, 0, 0)'})


# Run the app
if __name__ == '__main__':
    app.run_server(debug=False)
