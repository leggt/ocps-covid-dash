from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

d20212022 = {
    'file': 'data/2021-2022-cases.csv',
    'directory': 'data/directory.csv',
    'demographics': 'data/demographics.csv',
    'cutoff': datetime(2021, 8, 2)
}
d20202021 = {
    'file': 'data/2020-2021-cases.csv',
    'directory': 'data/directory.csv',
    'demographics': 'data/demographics.csv',
    'start_date': datetime(2021, 8, 1),
    'cutoff': datetime(2020, 8, 21)
}

df_to_dir_map = {
    'LAKECOMO': 'LAKECOMOSCHOOL',
    'AUDUBONPARK': 'AUDUBONPARKSCHOOL',
    'APOPKAMEMORIALMIDDLE': 'APOPKAMIDDLE',
    'WHEATLEYELEMENTARY': 'PHILLISWHEATLEYELEMENTARY',
    'DRPHILLIPSHIGH': 'DRPHILLIPSHIGH',
    'DILLARDELEMENTARY': 'DILLARDSTREETELEMENTARY',
    'NORTHLAKEPARKCOMMUNITY': 'NORTHLAKEPARKCOMMUNITYELEMENTARY',
    'WINTERPARK9THGRADECENTER': 'WINTERPARKHIGH9THGRADECENTER'
}

df_to_demo_map = {
    'LAKECOMO': 'LAKECOMOSCHOOL',
    'AUDUBONPARK': 'AUDUBONPARKSCHOOL',
    'APOPKAMEMORIALMIDDLE': 'APOPKAMIDDLE',
    'WHEATLEYELEMENTARY': 'PHILLISWHEATLEYELEMENTARY',
    'DRPHILLIPSHIGH': 'DRPHILLIPSHIGH',
    'DILLARDELEMENTARY': 'DILLARDSTREETELEMENTARY',
    'NORTHLAKEPARKCOMMUNITY': 'NORTHLAKEPARKCOMMUNITYELEMENTARY',
    'OCVSVIRTUALFRANCHISE': 'ORANGECOUNTYVIRTUAL',
    'PIEDMONTLAKES': 'PIEDMONTLAKESMIDDLE',
    'WINTERPARK9THGRADECENTER': 'WINTERPARKHIGH9THGRADECENTER'
}

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


def mapDirNames(name, name_map):
    name = name.upper()
    name = name.replace('K-8', '')
    name = name.replace("ST.", "")
    name = name.replace('SCHOOLS', '')
    name = name.replace('SCHOOL', '')
    name = name.replace('(', '')
    name = name.replace(')', '')
    name = name.replace("’", "")
    name = name.replace("-", "")
    name = name.replace(".", "")
    name = name.replace(' ', '')

    if name in name_map:
        return name_map[name]

    return name.strip()


class Data:
    def __init__(self, dataset):
        self.dataset = dataset
        df = pd.read_csv(dataset['file'])
        df['date'] = df['date'].apply(pd.to_datetime)
        df['count'] = df['count'].apply(pd.to_numeric)

        dir_df = pd.read_csv(dataset['directory'])

        demo_df = pd.read_csv(dataset['demographics'], usecols=[
                              'date', 'location', 'total'])
        demo_df['date'] = demo_df['date'].apply(pd.to_datetime)

        df['location_map'] = df.location.apply(
            lambda x: mapDirNames(x, df_to_dir_map))
        demo_df['location_map'] = demo_df.location.apply(
            lambda x: mapDirNames(x, df_to_demo_map))
        del demo_df['location']
        dir_df['location_map'] = dir_df.location.apply(
            lambda x: mapDirNames(x, df_to_dir_map))

        df = df.merge(dir_df, how='left', on='location_map')
        df = df.sort_values(by='date')
        demo_df = demo_df.sort_values(by='date')
        df = pd.merge_asof(df, demo_df, on='date',
                           by='location_map', direction='nearest')

        df.rename(columns={'location_x': 'location',
                  'total': 'student_count', 'count': 'confirmed'}, inplace=True)
        df.drop(['location_map', 'location_y'], axis=1, inplace=True)

        self.df = df

    def getLatestDate(self):
        return self.df.date.max().date()

    def getLocationsList(self):
        return self.df.location.sort_values().unique().tolist()

    def getTotalConfirmedCases(self):
        return self.df.confirmed.sum()

    def getTotalEmployeeCases(self):
        return self.df[self.df.type == 'Employee'].confirmed.sum()

    def getTotalStudentCases(self):
        return self.df[self.df.type == 'Student'].confirmed.sum()

    def getTotalVendorVisitorCases(self):
        return self.df[self.df.type == 'Vendor/Visitor'].confirmed.sum()


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
                     title="Confirmed cases by type", color_discrete_map=color_map_by_type)
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
                     title="Confirmed cases by school level", color_discrete_map=color_map_by_level)
        fig.update_layout(legend=self.legend, xaxis_title="", yaxis_title="")
        return fig

    def plotBySchool(self, schools=[]):
        df = self.df
        df = df[df.date >= datetime(2000, 1, 1)]
        df = df.dropna()
        if len(schools) > 0:
            df = df[df.location.isin(schools)]

        fig = px.bar(df, x='date', y='confirmed', color='location',
                     title="Confirmed cases by school")
        fig.update_layout(legend=self.legend, xaxis_title="", yaxis_title="")
        return fig

    def plotBox(self):
        all = self.df.groupby(by=['level', 'location'])[
            'confirmed'].sum().reset_index().copy()
        # TODO why can't I do this before grouping?
        all['level'] = pd.Categorical(
            all['level'], ['Elementary', 'Middle', 'High'])
        all = all.sort_values(by='level')

        fig = px.box(all, x='confirmed', y='level', color='level', points='all',
                     hover_name='location', title="Distribution of confirmed cases by school level", color_discrete_map=color_map_by_level)
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
                    marker={'color': self.getColorForLevel(level)})

        fig.add_bar(x=df['confirmed'], y=df['location'], row=2, col=1, name="Schools", marker={
                    'color': self.getColorForLevel(level)})
        fig.update_yaxes(visible=False)
        fig.update_xaxes(visible=True, row=1, col=1,
                         showticklabels=True, title="")
        fig.update_xaxes(visible=True, row=2, col=1, showticklabels=True,
                         title_text="Total # of confirmed cases by school")
        fig.update_layout(
            title_text="%s Schools Confirmed Cases Distribution" % (level))

        return fig

    def getColorForType(self, type):
        return color_map_by_type[type]

    def getColorForLevel(self, level):
        return color_map_by_level[level]


if __name__ == "__main__":
    d = Data(d20212022)
    locs = d.getLocationsList()
    pass
