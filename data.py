from datetime import datetime

import pandas as pd

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

        demo_df = pd.merge(
            demo_df, df[['location', 'location_map']], on='location_map')
        del demo_df['location_map']
        demo_df = demo_df.sort_values(by='date')
        self.demo_df = demo_df.drop_duplicates()

        df = df.merge(dir_df, how='left', on='location_map')
        df = df.sort_values(by='date')

        df.rename(columns={'location_x': 'location',
                  'total': 'student_count', 'count': 'confirmed'}, inplace=True)
        df.drop(['location_map'], axis=1, inplace=True)

        self.df = df

    def getLatestDate(self):
        return self.df.date.max().date()

    def getLocationsList(self):
        return self.df.location.sort_values().unique().tolist()

    def getSchoolPerCapita(self, school):
        latest = self.getLatestDate()
        demo_df = self.demo_df.set_index('date').sort_index()
        return demo_df[demo_df.location == school].asof(pd.to_datetime(latest)).total

    def getTotalPerCapita(self):
        latest = pd.to_datetime(self.getLatestDate())
        demo_df = self.demo_df
        latest = demo_df[demo_df.date <= latest].date.max()
        return demo_df[demo_df.date == latest].total.sum()

    def getTotalsForSchool(self, school):
        df = self.df[self.df.location == school]
        pc = self.getSchoolPerCapita(school)
        tc = self.getTotalConfirmedCases(df)
        te = self.getTotalEmployeeCases(df)
        ts = self.getTotalStudentCases(df)
        tv = self.getTotalVendorVisitorCases(df)
        return (
            tc, te, ts, tv, pc
        )

    def getTotalConfirmedCases(self, df=None):
        if df is None:
            df = self.df
        return df.confirmed.sum()

    def getTotalEmployeeCases(self, df=None):
        if df is None:
            df = self.df
        return df[df.type == 'Employee'].confirmed.sum()

    def getTotalStudentCases(self, df=None):
        if df is None:
            df = self.df
        return df[df.type == 'Student'].confirmed.sum()

    def getTotalVendorVisitorCases(self, df=None):
        if df is None:
            df = self.df
        return df[df.type == 'Vendor/Visitor'].confirmed.sum()

    def getLevelForSchool(self, school):
        df = self.df
        return df['level'][df.location == school].unique()[0]


if __name__ == "__main__":
    d = Data(d20212022)
    locs = d.getLocationsList()
    pass
