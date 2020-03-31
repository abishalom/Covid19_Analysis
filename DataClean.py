import plotly.express as px
import numpy as np
import pandas as pd
import pickle

#Helper function
def get_divide_cols_fn(c1, c2, res):
    def f(df):
        df[res] = df[c1]/df[c2]
        return df
    return f

def get_JHU_data(name):
    jhu_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_{}_global.csv'.format(name)
    jhu_df = pd.read_csv(jhu_url, error_bad_lines = False)

    jhu_df = jhu_df.groupby('Country/Region').sum().drop(['Lat', 'Long'], axis=1)
    jhu_df = jhu_df.stack().rename(name.capitalize()).to_frame()

    jhu_df.index = jhu_df.index.rename(['Country', 'Date'])
    jhu_df.index = jhu_df.index.set_levels([jhu_df.index.levels[0], pd.to_datetime(jhu_df.index.levels[1])])

    return jhu_df

def get_us_data():
    url = 'https://covidtracking.com/api/us/daily.csv'
    us_df = pd.read_csv(url, index_col = 0)
    us_df.index = pd.to_datetime(us_df.index, format = '%Y%m%d').rename('Date')
    us_df = us_df.sort_index()

    col_map = {
        'positive': 'Confirmed',
        'totalTestResults': 'TotalTests',
        'hospitalized': 'Hospitalized',
        'death': 'Deaths'
    }

    us_df = us_df[list(col_map.keys())].rename(mapper=  col_map, axis=1)    
    us_df['Country'] = 'US'
    us_df = us_df.set_index([us_df.Country, us_df.index]).drop(['Country'], axis=1)

    return us_df

def get_italy_data():
    url = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale.csv'
    italy_df = pd.read_csv(url, index_col = 0)
    italy_df.index = pd.to_datetime(italy_df.index).normalize().rename('Date')
    col_map = {
        'dimessi_guariti': 'Recovered',
        'totale_ospedalizzati': 'Hospitalized',
        'isolamento_domiciliare': 'Home',
        'tamponi': 'TotalTests',
        'stato': 'Country',
        'totale_casi': 'Confirmed',
        'deceduti': 'Deaths'
    }
    italy_df = italy_df[list(col_map.keys())].rename(mapper =  col_map, axis=1)
    italy_df.Country = 'Italy'
    italy_df = italy_df.set_index([italy_df.Country, italy_df.index]).drop(['Country'], axis=1)

    return italy_df

def join_dfs(default, other):
    #For joining dataframes, using one as default and filling in missing data
    overlap = set(default.columns).intersection(set(other.columns))
    default = pd.merge(default, other, left_index=True, right_index = True, how = 'outer', suffixes = ('', '_other'))
    for col in overlap:
        default[col] = default[col].combine_first(default[col + '_other'])

    default = default.drop([col + '_other' for col in overlap], axis=1)

    return default

def get_pop_dict():
    pop = pd.read_csv('WPP2019_TotalPopulationBySex.csv')
    pop = pop[pop.Time.eq(2020) & pop.Variant.eq('Medium')][['Location', 'PopTotal']].set_index('Location')
    pop.columns = ['Population']
    pop.loc['Diamond Princess'] = 3700

    aliases = {
        'US': 'United States of America',
        'Iran': 'Iran (Islamic Republic of)',
        'Bolivia': 'Bolivia (Plurinational State of)',
        'Brunei': 'Brunei Darussalam',
        'Korea, South': 'Republic of Korea',
        'Moldova': 'Republic of Moldova',
        'Russia': 'Russian Federation',
        "Cote d'Ivoire": "Côte d'Ivoire",
        'Syria': 'Syrian Arab Republic',
        'Tanzania': 'United Republic of Tanzania',
        'West Bank and Gaza': 'State of Palestine',
        'Venezuela': 'Venezuela (Bolivarian Republic of)',
        'Vietnam': 'Viet Nam',
        'Taiwan*': 'China, Taiwan Province of China',
        'Congo (Brazzaville)': 'Congo',
        'Congo (Kinshasa)': 'Democratic Republic of the Congo'
    }

    aliases = {v:k for k, v in aliases.items()}
    pop = pop.rename(mapper = aliases, axis=0) * 1000
    return pop

def merge_pop(df):
    pop = get_pop_dict()
    df = df.merge(pop, how = 'left', left_on = 'Country', right_index = True)
    return df

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

    #Get Hopkins data
    jhu_df = get_JHU_data('confirmed')
    jhu_death_df = get_JHU_data('deaths')
    jhu_df = jhu_death_df.join(jhu_df)
    jhu_death_df = None

    #Join the dataframes, add US and Italy data from source.
    dat = join_dfs(dat, get_us_data())
    dat = join_dfs(dat, get_italy_data())
    dat = join_dfs(dat, jhu_df)
    jhu_df = None
    dat = merge_pop(dat)

    #Tens of thousands of population
    dat['Pop10k'] = dat['Population'] / 10000

    #Add New Cases, New Tests
    dat['NewCases'] = dat.groupby('Country')['Confirmed'].diff()
    dat['NewTests'] = dat.groupby('Country')['TotalTests'].diff()
    dat['NewDeaths'] = dat.groupby('Country')['Deaths'].diff()
    dat['DaysSinceFirst'] = (dat['Confirmed'] >= 1).groupby('Country').cumsum().replace(0, np.nan) - 1
    dat['ConfirmedGrowth'] = dat.groupby('Country')['Confirmed'].pct_change() * 100.
    dat['DaysSinceTenthDeath'] = (dat['Deaths'] >= 10).groupby('Country').cumsum().replace(0, np.nan)

    dat = dat.groupby('Country').apply(get_divide_cols_fn("NewCases", "NewTests", "DailyPosTestRate"))
    dat = dat.groupby('Country').apply(get_divide_cols_fn("Confirmed", "TotalTests", "CumulativePosTestRate"))
    dat = dat.groupby('Country').apply(get_divide_cols_fn("Deaths", "Confirmed", "CumulativeDeathRate"))
    dat = dat.groupby('Country').apply(get_divide_cols_fn('Hospitalized', 'Confirmed', 'HospitalizationRate'))
    dat = dat.groupby('Country').apply(get_divide_cols_fn('TotalTests', 'Pop10k', 'TotalTestsPer10k'))
    dat = dat.groupby('Country').apply(get_divide_cols_fn('Confirmed', 'Pop10k', 'ConfirmedPer10k'))
    dat = dat.groupby('Country').apply(get_divide_cols_fn('NewTests', 'Pop10k', 'NewTestsPer10k'))

    #Days Since Shutdown
    dat['DaysSinceShutdown'] = np.nan
    x = (dat[dat['Shutdown'] == 1]).groupby('Country').shift(0)
    s_countries = list(x.index.get_level_values(0))

    for s in s_countries:
        old = x.xs(s, level=0).index[0]
        first = dat.xs(s, level=0).index[0]
        d = len(dat.xs(s, level=0).loc[first:old].index)
        new = dat.xs(s, level=0).Shutdown.shift(-d + 1).fillna(1).cumsum() - (d)
        dat.loc[s]['DaysSinceShutdown'] = new

    #Keep the ones with more than 1 confirmed day
    dat = dat[dat['Confirmed'] >= 1]

    #Set the index
    dat = dat.set_index([dat.index, "DaysSinceFirst", "DaysSinceTenthDeath", "DaysSinceShutdown"
                        ]).reorder_levels(["Country", "DaysSinceFirst", "DaysSinceTenthDeath", "DaysSinceShutdown",
                                        "Date"]).sort_index()
    #Pickle object, return success
    pickle.dump(dat, open(out_file, 'wb'))

    return 1

# sched = BackgroundScheduler()

# @sched.scheduled_job('cron', day_of_week='mon-sun',  hour = 23)
# def scheduled_job():
#     data_clean('compiled_data.p')

if __name__ == "__main__":
    # sched.start()
    data_clean('compiled_data.p')