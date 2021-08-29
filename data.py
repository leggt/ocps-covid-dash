from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

d20212022 = {
    'file': 'data/2021-2022-cases.csv',
    'directory': 'data/directory.csv',
    'cutoff': datetime(2021, 8, 2)
}
d20202021 = {
    'file': 'data/2020-2021-cases.csv',
    'directory': 'data/directory.csv',
    'start_date': datetime(2021, 8, 1),
    'cutoff': datetime(2020, 8, 21)
}

name_map = {
    'LAKE COMO K-8': 'LAKE COMO SCHOOL',
    'AUDUBON PARK K-8': 'AUDUBON PARK SCHOOL',
    'APOPKA MEMORIAL MIDDLE': 'MEMORIAL MIDDLE',
    'WHEATLEY ELEMENTARY': 'PHILLIS WHEATLEY ELEMENTARY',
    'DR. PHILLIPS HIGH': 'DR PHILLIPS HIGH',
    'DILLARD ST. ELEMENTARY': 'DILLARD STREET ELEMENTARY',
    'NORTHLAKE PARK COMMUNITY': 'NORTHLAKE PARK COMMUNITY ELEMENTARY',
    'WINTER PARK 9TH GRADE CENTER': 'WINTER PARK HIGH 9TH GRADE CENTER'
}

class Data:
    def __init__(self, dataset):
        self.dataset = dataset
        df = pd.read_csv(dataset['file'])
        df['date'] = df['date'].apply(pd.to_datetime)
        df['count'] = df['count'].apply(pd.to_numeric)
        self.df = df

        dir_df = pd.read_csv(dataset['directory'])
        self.df['location_map'] = self.df.location.apply(lambda x: self.mapDirNames(x))
        self.df = self.df.merge(dir_df, how='left', left_on='location_map',right_on='location',suffixes=(None,"_"))
        self.df.drop(columns=["location_","location_map"],inplace=True)

    def getLatestDate(self):
        return self.df.date.max().date()

    def getLocationsList(self):
        return self.df.location.sort_values().unique().tolist()

    def mapDirNames(self, name):
        name = name.upper()
        name = name.replace('(', '')
        name = name.replace(')', '')
        name = name.replace(" SCHOOL", "")
        name = name.replace("’", "")

        if name in name_map:
            return name_map[name]

        return name.strip()

class Plots:
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
    def __init__(self,data):
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
        all = df.groupby(by=['date', 'type'])['count'].sum().reset_index()
        fig = px.bar(all, x='date', y='count', color='type', title="Confirmed cases by type")
        fig.update_layout(legend=self.legend,xaxis_title="",yaxis_title="")
        return fig

    def plotByLevel(self):
        df = self.df
        df = df[df.date >= datetime(2000, 1, 1)]
        df = df.dropna()
        all = df.groupby(by=['date', 'level'])[
            'count'].sum().reset_index()
        fig = px.bar(all,x='date',y='count',color='level',title="Confirmed cases by school level")
        fig.update_layout(legend=self.legend,xaxis_title="",yaxis_title="")
        return fig

    def plotBySchool(self,schools=[]):
        df = self.df
        df = df[df.date >= datetime(2000, 1, 1)]
        df = df.dropna()
        if len(schools) > 0:
            df=df[df.location.isin(schools)]
        
        fig = px.bar(df,x='date',y='count',color='location',title="Confirmed cases by school")
        fig.update_layout(legend=self.legend,xaxis_title="",yaxis_title="")
        return fig

    def plotBox(self):
        all = self.df.groupby(by=['level','location'])['count'].sum().reset_index()

        fig = px.box(all, x='count', y='level', color='level', points='all', hover_name='location',title="Distribution of confirmed cases by school level")
        fig.update_layout(legend=self.legend)
        return fig

    def plotMap(self,filter=[]):
        df = self.df
        df_bycount = df.groupby(
            ['location', 'level', 'lat', 'long']).sum(['count'])
        df_bycount.dropna()
        df = df_bycount.reset_index()

        fig = px.scatter_mapbox(df, lat="lat", lon="long",
                                color_discrete_sequence=["red", "yellow", "blue"], zoom=9, color='level', size='count', size_max=50, opacity=.5, hover_name='location', hover_data=['level', 'count'])

        fig.update_layout(mapbox_style="open-street-map")
        fig.update_layout(autosize=True,legend=self.legend,xaxis_title="",yaxis_title="")
        return fig

    
if __name__ == "__main__":
    d = Data(d20212022)
    locs = d.getLocationsList()
    pass
    
