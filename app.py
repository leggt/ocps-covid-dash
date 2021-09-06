import dash
import dash_bootstrap_components as dbc
from dash_bootstrap_components._components.Label import Label
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash_html_components.Div import Div
from data import *
from plots import *
from flask_caching import Cache
import sys

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP],
                # https://dash-bootstrap-components.opensource.faculty.ai/docs/faq/
                meta_tags=[
    {"name": "viewport", "content": "width=device-width, initial-scale=1"},
], suppress_callback_exceptions=True
)

cache = Cache(app.server, config={
    # try 'filesystem' if you don't want to setup redis
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': '_cache',
    # Cache is valid for a day. (Cache is cleared when we get new data in the nightly scripts)
    'CACHE_DEFAULT_TIMEOUT': 60*60*24
})

if len(sys.argv) > 1 and sys.argv[1] == 'debug':
    print("clearing cache")
    cache.clear()

navbar = dbc.NavbarSimple(
    brand="(Unofficial) OCPS Covid Dashboard",
    brand_href="/",
    color="dark",
    dark=True,
)

app.title = "(Unofficial) OCPS Covid Dashboard"
app.layout = html.Div(
    [
        dcc.Store(id="year_store", data={'year': '2021'}),
        dcc.Location(id='url', refresh=False),
        navbar,
        dbc.Nav([
            dbc.NavItem(dbc.NavLink("About", href="/about", active='exact')),
            dbc.NavItem(dbc.NavLink("Totals", href="/", active='exact')),
            dbc.NavItem(dbc.NavLink(
                "By School", href="/school", active='exact')),
            dbc.NavItem(dbc.NavLink("Map", href="/map", active='exact')),
            dbc.DropdownMenu(
                label="2021-2022",
                children=[
                    dbc.DropdownMenuItem("2021-2022", id="y2021"),
                    dbc.DropdownMenuItem("2020-2021", id="y2020"),
                ],
                id='year_dd'
            )
        ], pills=True, fill=True),
        html.Hr(),
        html.Div(id="main_content", children=[])
    ]
)


@cache.memoize()
def getDataPlots(dataset):
    data = Data(dataset)
    plots = Plots(data)
    return data, plots


@cache.memoize()
def showGraphs(dataset):
    data, plots = getDataPlots(dataset)

    children = [
        getTotals(data.getTotalConfirmedCases(), data.getTotalEmployeeCases(
        ), data.getTotalStudentCases(), data.getTotalVendorVisitorCases(), data.getTotalPerCapita()),
        dbc.Row([dbc.Col(dbc.Card(
            [dbc.CardHeader(html.B("Confirmed cases by Type")), ]), align='center')]),
        dcc.Graph(id="type_count", figure=plots.plotByType()),
        dbc.Row([dbc.Col(dbc.Card(
            [dbc.CardHeader(html.B("Confirmed cases by Level")), ]), align='center')]),
        dcc.Graph(id="level_count", figure=plots.plotByLevel()),

        dbc.Row([dbc.Col(dbc.Card(
            [dbc.CardHeader(html.B("Distribution of cases by Level")), ]), align='center')]),
        dcc.Graph(id="box_plot", figure=plots.plotDistribution()),
        dbc.Row([dbc.Col(dbc.Card([dbc.CardHeader(html.B(
            "Distribution of confirmed cases in Elementary schools")), ]), align='center')]),
        dcc.Graph(
            figure=plots.plotDistributionByLevel('Elementary')),
        dbc.Row([dbc.Col(dbc.Card([dbc.CardHeader(html.B(
            "Distribution of confirmed cases in Middle schools")), ]), align='center')]),
        dcc.Graph(
            figure=plots.plotDistributionByLevel('Middle')),
        dbc.Row([dbc.Col(dbc.Card([dbc.CardHeader(html.B(
            "Distribution of confirmed cases in High schools")), ]), align='center')]),
        dcc.Graph(
            figure=plots.plotDistributionByLevel('High')),


    ]

    return children


def getTotals(total, employee, student, vendor, per_capita, margin="5px"):
    return html.Div([
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(html.B("Total")),
                    dbc.CardBody(html.B(total))
                ])),
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(html.B("Employee")),
                    dbc.CardBody(html.B(employee))
                ], color=getColorForType("Employee"))),
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(html.B("Student (%)")),
                    dbc.CardBody(html.B("%d (%.2f%%)" %
                                 (student, student/per_capita*100)))
                ], color=getColorForType("Student"))),
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(html.B("Vendor/Visitor")),
                    dbc.CardBody(html.B(vendor))
                ], color=getColorForType("Vendor/Visitor")))
        ])], style={'margin': margin})


@cache.memoize()  # in seconds
def showMap(dataset):
    _, plots = getDataPlots(dataset)
    return [
        dcc.Graph(id="map", figure=plots.plotMap(), style={'height': '100vh'})
    ]


def showAbout():
    with open("ABOUT.md", "r") as f:
        about = f.read()
    return [
        dbc.Row([
            dbc.Col([dcc.Markdown(about)], width={
                    "size": 10, "offset": 1}, align='center')
        ])
    ]


def showSchools(dataset):
    data = Data(dataset)

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


@cache.memoize()  # in seconds
def updateSchools(dataset, schools=[]):
    if len(schools) > 0:
        data, plots = getDataPlots(dataset)

        ret = []
        for school in schools:
            ret.extend([
                dbc.Row([
                    dbc.Col(
                        dbc.Card([
                            dbc.CardHeader(html.B(school)),
                            dbc.CardBody([
                                getTotals(
                                    *data.getTotalsForSchool(school), "5px 50px 5px"),
                                dcc.Graph(
                                    id="type_count", figure=plots.plotBySchool(school)),
                                dcc.Graph(
                                    figure=plots.plotDistributionsForSchool(school))
                            ])
                        ]))
                ])
            ])

        return ret
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
    if url is not None and url == "/about":
        return year, showAbout()
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
