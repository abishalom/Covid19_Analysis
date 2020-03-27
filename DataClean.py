import plotly.express as px
import numpy as np
import pandas as pd
import pickle
from apscheduler.schedulers.background import BackgroundScheduler

#Helper function
def get_divide_cols_fn(c1, c2, res):
    def f(df):
        df[res] = df[c1]/df[c2]
        return df
    return f

def data_clean(out_file):
    #Load initial Data
    dat = pd.read_csv('Covid19_Data.csv', index_col = 0)
    dat.index = pd.to_datetime(dat.index)

    col = dat.columns.str.split('_', expand=True)
    dat.columns = col
    dat.index = dat.index.rename("Date")
    dat.columns = dat.columns.rename(['Country', 'Col'])
    dat = dat.stack(level=0)
    dat.index = dat.index.reorder_levels(['Country', 'Date'])

    #Clean Hopkins Data
    jhu_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
    jhu_df = pd.read_csv(jhu_url, error_bad_lines = False)

    jhu_df = jhu_df.groupby('Country/Region').sum().drop(['Lat', 'Long'], axis=1)
    jhu_df = jhu_df.stack().rename('Confirmed').to_frame()

    jhu_df.index = jhu_df.index.rename(['Country', 'Date'])
    jhu_df.index = jhu_df.index.set_levels([jhu_df.index.levels[0], pd.to_datetime(jhu_df.index.levels[1])])

    jhu_death_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
    jhu_death_df = pd.read_csv(jhu_death_url, error_bad_lines = False)

    jhu_death_df = jhu_death_df.groupby('Country/Region').sum().drop(['Lat', 'Long'], axis=1)
    jhu_death_df = jhu_death_df.stack().rename('Dead').to_frame()

    jhu_death_df.index = jhu_death_df.index.rename(['Country', 'Date'])
    jhu_death_df.index = jhu_death_df.index.set_levels([jhu_death_df.index.levels[0], pd.to_datetime(jhu_death_df.index.levels[1])])

    jhu_df = jhu_death_df.join(jhu_df)
    jhu_death_df = None

    #Combine the datasets
    dat = pd.merge(dat, jhu_df, left_index=True, right_index=True, how = 'outer', suffixes = ('', '_JHU'))
    dat['Confirmed'] = dat['Confirmed'].combine_first(dat['Confirmed_JHU'])
    dat['Dead'] = dat['Dead'].combine_first(dat['Dead_JHU'])


    dat = dat.drop(['Confirmed_JHU', 'Dead_JHU'], axis=1)

    #Add New Cases, New Tests
    dat['NewCases'] = dat.groupby('Country')['Confirmed'].diff()
    dat['NewTests'] = dat.groupby('Country')['TotalTests'].diff()
    dat['DaysSinceFirst'] = (dat['Confirmed'] >= 1).groupby('Country').cumsum().replace(0, np.nan)
    dat['ConfirmedGrowth'] = dat.groupby('Country')['Confirmed'].pct_change() * 100.
    dat['DaysSinceTenthDeath'] = (dat['Dead'] >= 10).groupby('Country').cumsum().replace(0, np.nan)

    dat = dat.groupby('Country').apply(get_divide_cols_fn("NewCases", "NewTests", "DailyPosTestRate"))
    dat = dat.groupby('Country').apply(get_divide_cols_fn("Confirmed", "TotalTests", "CumulativePosTestRate"))

    #Days Since Shutdown
    dat['DaysSinceShutdown'] = np.nan
    x = (dat[dat['Shutdown'] == 1]).groupby('Country').shift(0)
    s_countries = list(x.index.get_level_values(0))

    for s in s_countries:
        #Find d
        old = x.xs(s, level=0)
        d = (old.index[x['Shutdown'] == 1] - dat.index[0][1]).days[0]
        new = dat.xs(s, level=0).Shutdown.shift(-d+2).fillna(1).cumsum() - (d-1)
        dat.loc[s]['DaysSinceShutdown'] = new

    dat = dat[dat['Confirmed'] >= 1]

    #Set the index
    dat = dat.set_index([dat.index, "DaysSinceFirst", "DaysSinceTenthDeath", "DaysSinceShutdown"
                        ]).reorder_levels(["Country", "DaysSinceFirst", "DaysSinceTenthDeath", "DaysSinceShutdown",
                                        "Date"]).sort_index()
    #Pickle object, return success
    pickle.dump(dat, open(out_file, 'wb'))

    return 1

sched = BackgroundScheduler()

@sched.scheduled_job('cron', day_of_week='mon-sun',  hour = 23)
def scheduled_job():
    data_clean('compiled_data.p')

if __name__ == "__main__":
    sched.start()
    # data_clean('compiled_data.p')