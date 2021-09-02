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


if __name__ == "__main__":
    d = Data(d20212022)
    locs = d.getLocationsList()
    pass
