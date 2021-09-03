from datetime import datetime
from data import *

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

color_map_by_level = {
    'Elementary': px.colors.qualitative.Plotly[0],
    'Middle': px.colors.qualitative.Plotly[1],
    'High': px.colors.qualitative.Plotly[2],
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
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )

    def __init__(self, data):
        self.data = data
        self.df = self.getMapData()

    def getMapData(self):
        df = self.data.df
        df = df[df.date >= datetime(2000, 1, 1)]
        df = df.dropna()
        return df

    def plotByType(self):
        df = self.df
        df = df[df.date >= datetime(2000, 1, 1)]
        df = df.dropna()
        all = df.groupby(by=['date', 'type'])['confirmed'].sum().reset_index()
        fig = px.bar(all, x='date', y='confirmed', color='type',
                     color_discrete_map=color_map_by_type)
        fig.update_layout(legend=self.legend, xaxis_title="", yaxis_title="")
        return fig

    def plotByLevel(self):
        df = self.df
        df = df[df.date >= datetime(2000, 1, 1)]
        df = df.dropna()
        all = df.groupby(by=['date', 'level'])[
            'confirmed'].sum().reset_index()
        all['level'] = pd.Categorical(
            all['level'], ['Elementary', 'Middle', 'High'])
        all = all.sort_values(by='level')
        fig = px.bar(all, x='date', y='confirmed', color='level',
                     color_discrete_map=color_map_by_level)
        fig.update_layout(legend=self.legend, xaxis_title="", yaxis_title="")
        return fig

    def plotRollupBySchool(self, schools=[]):
        df = self.df
        df = df[df.date >= datetime(2000, 1, 1)]
        df = df.dropna()
        if len(schools) > 0:
            df = df[df.location.isin(schools)]

        df = df[['date', 'location', 'confirmed']]
        df = df.groupby(['date', 'location']).sum().reset_index()

        fig = px.bar(df, x='date', y='confirmed', color='location')
        fig.update_layout(legend=self.legend, xaxis_title="", yaxis_title="")
        return fig

    def plotDistribution(self):
        all = self.df.groupby(by=['level', 'location'])[
            'confirmed'].sum().reset_index().copy()
        # TODO why can't I do this before grouping?
        all['level'] = pd.Categorical(
            all['level'], ['Elementary', 'Middle', 'High'])
        all = all.sort_values(by='level')

        fig = px.box(all, x='confirmed', y='level', color='level', points='all',
                     hover_name='location',  color_discrete_map=color_map_by_level)
        fig.update_layout(legend=self.legend, xaxis_title="", yaxis_title="")
        return fig

    def plotMap(self, filter=[]):
        df = self.df
        df_bycount = df.groupby(
            ['location', 'level', 'lat', 'long']).sum(['confirmed'])
        df_bycount.dropna()
        df = df_bycount.reset_index()

        fig = px.scatter_mapbox(df, lat="lat", lon="long",
                                color_discrete_map=color_map_by_level, zoom=9, color='level', size='confirmed', size_max=50, opacity=.75, hover_name='location', hover_data=['level', 'confirmed'])

        fig.update_layout(mapbox_style="open-street-map")
        fig.update_layout(autosize=True, legend=self.legend,
                          xaxis_title="", yaxis_title="")
        return fig

    def plotDistributionByLevel(self, level):
        df = self.df
        df = df[['level', 'location', 'confirmed']].groupby(
            ['level', 'location']).sum().reset_index()
        df = df[df.level == level]

        fig = make_subplots(rows=4, cols=1, shared_xaxes=True, shared_yaxes=False,
                            specs=[[{}], [{"rowspan": 3}], [None], [None]],
                            )
        fig.add_box(x=df['confirmed'], name=level, row=1, col=1,
                    marker={'color': getColorForLevel(level)})

        fig.add_bar(x=df['confirmed'], y=df['location'], row=2, col=1, name="Schools", marker={
                    'color': getColorForLevel(level)})
        fig.update_yaxes(visible=False)
        fig.update_xaxes(visible=True, row=1, col=1,
                         showticklabels=True)
        fig.update_xaxes(visible=True, row=2, col=1, showticklabels=True,
                         title_text="Total # of confirmed cases by school")

        return fig
