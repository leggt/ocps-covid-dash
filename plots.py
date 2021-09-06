from datetime import datetime
from data import *

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objs import layout
from plotly.subplots import make_subplots

color_map_by_level = {
    'Elementary': px.colors.qualitative.Plotly[0],
    'Middle': px.colors.qualitative.Plotly[1],
    'High': px.colors.qualitative.Plotly[2],
    'All': px.colors.qualitative.Plotly[6],
}
color_map_by_type = {
    'Student': px.colors.qualitative.Plotly[3],
    'Employee': px.colors.qualitative.Plotly[4],
    'Vendor/Visitor': px.colors.qualitative.Plotly[5],
}


def getColorForType(type):
    return color_map_by_type[type]


def getColorForLevel(level):
    return color_map_by_level[level]


class Plots:
    legend = dict(
        orientation="h",
        yanchor="top",
        y=-.05,
        xanchor="right",
        x=1
    )

    margin = {'l': 5, 'r': 5, 'b': 50, 't': 50}

    def __init__(self, data):
        self.data = data
        self.df = self.getMapData()

    def getMapData(self):
        df = self.data.df
        df = df[df.date >= datetime(2000, 1, 1)]
        df = df.dropna()
        return df

    def plotBy(self, title, color_column, color_order, color_map, plot_df=None, demo_df=None):
        fig = go.Figure()
        if plot_df is None:
            plot_df = self.df

        if demo_df is None:
            demo_df = self.data.demo_df

        new_count = 0
        # New cases
        for typ in color_order:
            df = plot_df
            df = df[df[color_column] == typ]
            if df.empty:
                continue
            new_count = new_count+1
            df = df.groupby('date').confirmed.sum().reset_index()

            fig.add_bar(x=df['date'], y=df.confirmed, name=typ,
                        marker={'color': color_map[typ]})

        cum_count = 0
        # Cumulative
        for typ in color_order:
            df = plot_df
            df = df[df[color_column] == typ]
            if df.empty:
                continue
            cum_count = cum_count+1
            df = df[['date', 'confirmed']].groupby(
                ['date']).confirmed.sum().reset_index()
            df.confirmed = df.confirmed.cumsum()

            fig.add_bar(x=df['date'], y=df.confirmed, name=typ,
                        visible=False, marker={'color': color_map[typ]})

        cum_pc_count = 0
        # Cumulative per capita
        for typ in color_order:
            df = plot_df
            df = df[df[color_column] == typ]
            if df.empty:
                continue
            cum_pc_count = cum_pc_count+1
            df = df[['date', 'confirmed']].groupby(
                ['date']).confirmed.sum().reset_index()

            demo_df = demo_df[['date', 'total']].groupby(
                ['date']).total.sum().reset_index()
            df = pd.merge_asof(df, demo_df, on='date',
                               direction='nearest', suffixes=(None, "_y"))
            df['confirmed'] = df.apply(lambda x: x.confirmed/x.total, axis=1)
            df.confirmed = df.confirmed.cumsum()

            fig.add_bar(x=df['date'], y=df.confirmed, name=typ,
                        visible=False, marker={'color': color_map[typ]})

        fig.update_layout(legend=self.legend, xaxis_title="",
                          yaxis_title="", margin=self.margin)
        fig.layout.barmode = 'stack'

        new_vis = [True for x in range(new_count)]
        new_vis.extend([False for x in range(cum_count)])
        new_vis.extend([False for x in range(cum_pc_count)])

        cum_vis = [False for x in range(new_count)]
        cum_vis.extend([True for x in range(cum_count)])
        cum_vis.extend([False for x in range(cum_pc_count)])

        cum_pc_vis = [False for x in range(new_count)]
        cum_pc_vis.extend([False for x in range(cum_count)])
        cum_pc_vis.extend([True for x in range(cum_pc_count)])

        fig.update_layout(
            updatemenus=[
                dict(
                    buttons=list([
                        dict(
                            args=[
                                {"visible": new_vis},
                                {'yaxis.tickformat': '.0'}
                            ],
                            label="New cases",
                            method="update"
                        ),
                        dict(
                            args=[
                                {"visible": cum_vis},
                                {'yaxis.tickformat': '.0'}
                            ],
                            label="Cumulative",
                            method="update"
                        ),
                        dict(
                            args=[
                                {"visible": cum_pc_vis},
                                {'yaxis.tickformat': '.2%'}
                            ],
                            label="Cumulative per capita",
                            method="update"
                        ),
                    ]),
                    direction="down",
                    showactive=True,
                    xanchor="left",
                    x=0,
                    yanchor="bottom",
                    y=1.02
                ),
            ]
        )

        return fig

    def plotByType(self):
        return self.plotBy("Confirmed cases by Type", 'type', ['Employee', 'Student', 'Vendor/Visitor'], color_map_by_type)

    def plotByLevel(self):
        return self.plotBy("Confirmed cases by Level", 'level', ['Elementary', 'Middle', 'High'], color_map_by_level)

    def plotBySchool(self, school):
        df = self.df[self.df.location == school]
        demo_df = self.data.demo_df
        demo_df = demo_df[demo_df.location == school]
        return self.plotBy("%s confirmed cases by date" % (school), 'type', ['Employee', 'Student', 'Vendor/Visitor'], color_map_by_type, df, demo_df)

    def plotMap(self, filter=[]):
        df = self.df
        df_bycount = df.groupby(
            ['location', 'level', 'lat', 'long']).sum(['confirmed'])
        df_bycount.dropna()
        df = df_bycount.reset_index()

        fig = px.scatter_mapbox(df, lat="lat", lon="long",
                                color_discrete_map=color_map_by_level, zoom=9, color='level', size='confirmed', size_max=50, opacity=.75, hover_name='location', hover_data=['level', 'confirmed'])

        fig.update_layout(mapbox_style="open-street-map", margin=self.margin)

        legend = dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )

        fig.update_layout(autosize=True, legend=legend,
                          xaxis_title="", yaxis_title="")
        return fig

    def plotDistributionsForSchool(self, school):
        all = self.data.getDfTotalsByLocation()
        school_level = self.data.getLevelForSchool(school)
        by_level = all[all.level == school_level]
        by_school = all[all.location == school]
        confirmed = by_school.confirmed.sum()
        confirmed_pc = by_school.confirmed_pc.sum()

        fig = go.Figure()
        for t in [('All', all), (school_level, by_level)]:
            level = t[0]
            df = t[1]
            fig.add_box(x=df.confirmed, name=level,
                        marker={'color': getColorForLevel(level), 'opacity': .5}, legendgroup=level, hovertext=df.location)
            fig.add_scatter(x=[confirmed], y=[level], marker={'symbol': 'star', 'size': 8}, showlegend=False,
                            legendgroup=level, hovertemplate='%{hovertext}<br>Confirmed:%{x}<extra></extra>', hovertext=[school])

        for t in [('All', all), (school_level, by_level)]:
            level = t[0]
            df = t[1]
            fig.add_box(x=df.confirmed_pc, name=level, visible=False,
                        marker={'color': getColorForLevel(level), 'opacity': .5}, legendgroup=level, hovertext=df.location)
            fig.add_scatter(x=[confirmed_pc], y=[level], marker={'symbol': 'star', 'size': 8}, showlegend=False, visible=False,
                            legendgroup=level, hovertemplate='%{hovertext}<br>Confirmed:%{x}<extra></extra>', hovertext=[school])

        fig.update_layout(
            updatemenus=[
                dict(
                    buttons=list([
                        dict(
                            args=[
                                {"visible": [True, True, True, True,
                                             False, False, False, False]},
                                {'xaxis.tickformat': '.0'}
                            ],
                            label="By count",
                            method="update"
                        ),
                        dict(
                            args=[
                                {"visible": [False, False, False,
                                             False, True, True, True, True]},
                                {'xaxis.tickformat': '.2%'}
                            ],
                            label="Per capita",
                            method="update"
                        ),
                    ]),
                    direction="down",
                    showactive=True,
                    xanchor="left",
                    x=0,
                    yanchor="bottom",
                    y=1.02
                ),
            ])

        fig.update_yaxes(visible=False)
        fig.update_layout(
            legend=self.legend, margin=self.margin)

        return fig

    def plotDistributionByLevel(self, level):
        all = self.df
        all = all[['level', 'location', 'confirmed']].groupby(
            ['level', 'location']).sum().reset_index()

        if level != 'All':
            all = all[all.level == level]

        fig = make_subplots(rows=4, cols=1, shared_xaxes=False, shared_yaxes=False,
                            specs=[[{}], [{"rowspan": 3}], [None], [None]],
                            )
        fig.add_box(x=all['confirmed'], name=level, row=1, col=1,
                    marker={'color': getColorForLevel(level), 'opacity': .5}, showlegend=False)
        fig.update_layout(barmode='stack', margin=self.margin)
        fig.update_yaxes(visible=False)
        fig.update_xaxes(visible=True, row=1, col=1,
                         showticklabels=True)
        fig.update_xaxes(visible=True, row=2, col=1, showticklabels=True,
                         )

        fig.add_bar(x=all['confirmed'], y=[1 for x in all['confirmed']], row=2, col=1, marker={
                    'color': getColorForLevel(level), 'opacity': .5}, hovertemplate='%{hovertext}<br>Confirmed:%{x}<extra></extra>', hovertext=all['location'], showlegend=False)

        return fig

    def plotDistribution(self):
        all = self.data.getDfTotalsByLocation()

        fig = go.Figure()
        for level in ['High', 'Middle', 'Elementary']:
            df = all[all.level == level]
            fig.add_box(x=df['confirmed'], name=level,
                        marker={'color': getColorForLevel(level), 'opacity': .5}, legendgroup=level, hovertext=df.location)

        for level in ['High', 'Middle', 'Elementary']:
            df = all[all.level == level]
            fig.add_box(x=df['confirmed_pc'], name=level, visible=False,
                        marker={'color': getColorForLevel(level), 'opacity': .5}, legendgroup=level, hovertext=df.location)

        fig.update_layout(
            updatemenus=[
                dict(
                    buttons=list([
                        dict(
                            args=[
                                {"visible": [True, True, True,
                                             False, False, False]},
                                {'xaxis.tickformat': '.0'}
                            ],
                            label="By count",
                            method="update"
                        ),
                        dict(
                            args=[
                                {"visible": [False, False,
                                             False, True, True, True]},
                                {'xaxis.tickformat': '.2%'}
                            ],
                            label="Per capita",
                            method="update"
                        ),
                    ]),
                    direction="down",
                    showactive=True,
                    xanchor="left",
                    x=0,
                    yanchor="bottom",
                    y=1.02
                ),
            ]
        )

        fig.update_yaxes(visible=False)
        fig.update_layout(legend=self.legend, xaxis_title="",
                          yaxis_title="", margin=self.margin)
        return fig
