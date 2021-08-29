import dash
import dash_bootstrap_components as dbc
from dash_bootstrap_components._components.Label import Label
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from data import *
from flask_caching import Cache

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP],
                # https://dash-bootstrap-components.opensource.faculty.ai/docs/faq/
                meta_tags=[
    {"name": "viewport", "content": "width=device-width, initial-scale=1"},
], suppress_callback_exceptions=True
)

cache = Cache(app.server, config={
    # try 'filesystem' if you don't want to setup redis
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR' :'_cache'
})

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("All", href="/all")),
        dbc.NavItem(dbc.NavLink("By School", href="/school")),
        dbc.NavItem(dbc.NavLink("Map", href="/map")),
        dbc.DropdownMenu(
            label="2021-2022",
            children=[
                dbc.DropdownMenuItem("2021-2022", id="y2021"),
                dbc.DropdownMenuItem("2020-2021", id="y2020"),
            ],
            id='year_dd'
        )
    ],
    brand="(Unofficial) OCPS Covid Dashboard",
    brand_href="#",
    color="dark",
    dark=True,
)

app.title = "(Unofficial) OCPS Covid Dashboard"
app.layout = html.Div(
    [
        dcc.Store(id="year_store",data={'year':'2021'}),
        dcc.Location(id='url', refresh=False),
        navbar,
        html.Div(id="main_content", children=[])
    ]
)


@cache.memoize(timeout=600)  # in seconds
def showGraphs(dataset):
    plots = Plots(Data(dataset))

    return [
        dcc.Graph(id="type_count", figure=plots.plotByType()),
        dcc.Graph(id="level_count", figure=plots.plotByLevel()),
        dcc.Graph(id="box_plot", figure=plots.plotBox()),
    ]


@cache.memoize(timeout=600)  # in seconds
def showMap(dataset):
    plots = Plots(Data(dataset))
    return [
        dcc.Graph(id="map", figure=plots.plotMap(), style={'height': '100vh'})
    ]


def showSchools(dataset):
    data = Data(dataset)
    plots = Plots(data)

    all_schools = []
    for loc in data.getLocationsList():
        all_schools.append({'label': loc, 'value': loc})

    schools_dd = dcc.Dropdown(
        id='filter_schools',
        options=all_schools,
        value=[],
        placeholder="Filter..",
        multi=True
    )
    return html.Div([
        schools_dd,
        html.Div(
            children=updateSchools(dataset),
            id="schools_div"
        )
    ])


@cache.memoize(timeout=600)  # in seconds
def updateSchools(dataset, schools=[]):
    if len(schools) > 0:
        plots = Plots(Data(dataset))
        return [
            dcc.Graph(id="type_count", figure=plots.plotBySchool(schools)),
        ]
    else:
        return [dbc.Jumbotron(
            [
                html.H1("Filter by school", className="display-3"),
                html.P("Select a list of schools from the filter above to see some plots focusing on just those schools",
                    className="lead",
                ),
            ]
        )]


@app.callback(
    Output("year_store", "data"),
    [
        Input("y2021", "n_clicks_timestamp"),
        Input("y2020", "n_clicks_timestamp"),
    ]
)
def changeYear(y2021, y2020):
    if y2020 is not None and y2021 is None:
        return{'year': '2020'}  # Must have clicked 2020
    elif y2020 is not None and y2021 is not None and y2020 > y2021:
        return{'year': '2020'}  # Must have clicked 2020
    else:
        return {'year': '2021'}  # default


@app.callback(
    Output('year_dd', 'label'),
    Output("main_content", "children"),
    [Input('year_store', 'data'),
     Input('url', 'pathname'),
     ]
)
def display_router(data, url):
    dataset = getDataset(data)
    year = '2021-2022'
    if data is not None and data['year'] == '2020':
        year = '2020-2021'

    if url is not None and url == "/map":
        return year, showMap(dataset)
    if url is not None and url == "/school":
        return year, showSchools(dataset)
    else:
        return year, showGraphs(dataset)


def getDataset(data):
    if data is not None and data['year'] == '2020':
        return d20202021
    else:
        return d20212022


@app.callback(
    Output("schools_div", "children"),
    [Input("filter_schools", "value"),
     Input('year_store', 'data')]
)
def updateSchoolsFilter(schools, year):
    dataset = getDataset(year)
    return updateSchools(dataset, schools)

server = app.server

if __name__ == "__main__":
    app.run_server(debug=True, dev_tools_hot_reload=True)
    # app.run_server(debug=False, dev_tools_hot_reload=False)
