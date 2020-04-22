import plotly.express as px
import numpy as np
import pandas as pd
import pickle
import datetime
import zipfile
import requests
import io
import sys

#Helper function
def get_divide_cols_fn(c1, c2, res):
    def f(df):
        df[res] = df[c1]/df[c2]
        return df
    return f

def get_JHU_data(name, verbose = False):
    if verbose: print("Retrieving JHU {}".format(name))
    jhu_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_{}_global.csv'.format(name)
    jhu_df = pd.read_csv(jhu_url, error_bad_lines = False)

    jhu_df = jhu_df.groupby('Country/Region').sum().drop(['Lat', 'Long'], axis=1)
    jhu_df = jhu_df.stack().rename(name.capitalize()).to_frame()

    jhu_df.index = jhu_df.index.rename(['Country', 'Date'])
    jhu_df.index = jhu_df.index.set_levels([jhu_df.index.levels[0], pd.to_datetime(jhu_df.index.levels[1])])

    return jhu_df

def get_us_data(verbose = False):
    if verbose: print("Retrieving US data")
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

def get_italy_data(verbose = False):
    if verbose: print("Retrieving Italy data")
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

################################
# Below function too slow
################################
# def clean_mx_data(df, date):
#     """
#     Should return a row of a df, indexed by Date, Country (Mexico) with columns Confirmed,
#     Totaltests (confirmed + negative), Deaths. Hospitalization would also be nice.
#     """
#     result_df = {}

#     result_df['Date'] = date
#     result_df['Country'] = 'Mexico'
#     result_df['Confirmed'] = (df['RESULTADO'] == 1).sum()
#     result_df['TotalTests'] = (df['RESULTADO'] == 2).sum() + result_df['Confirmed']
#     result_df['Deaths'] = df.query('RESULTADO == 1 & FECHA_DEF != "9999-99-99"').FECHA_DEF.count()

#     result_df = pd.DataFrame(result_df, index = [0])

#     return result_df

# def get_mexico_data(days_backwards = 3, verbose = False):
    # end = datetime.date.today()
    # start = datetime.date.today() - datetime.timedelta(days = days_backwards)
    # dates_to_see = pd.date_range(start, end)

    # res = pd.DataFrame()

    # for d in dates_to_see:
    #     if verbose: print('Mexico pulling for {}'.format(d.strftime('%d-%m-%Y')))
    #     url = "http://187.191.75.115/gobmx/salud/datos_abiertos/historicos/datos_abiertos_covid19_{}.zip".format(
    #     d.strftime('%d.%m.%Y'))
    #     r = requests.get(url, stream = True)

    #     #fof represents 404 error on first try. Means we've reached last day of data.
    #     fof = r.status_code == 404
    #     if fof:
    #         #If it's not under historical, grab most recent
    #         r = requests.get("http://187.191.75.115/gobmx/salud/datos_abiertos/datos_abiertos_covid19.zip")

    #     f = zipfile.ZipFile(io.BytesIO(r.content))
    #     with f.open(f.namelist()[0]) as thefile:
    #         df = pd.read_csv(thefile)

    #     #Takes care of case when we had to go to recent df and it's yesterday's data.
    #     if fof and df.FECHA_ACTUALIZACION.iloc[0] != d:
    #         continue

    #     c = clean_mx_data(df, d)
    #     res = res.append(c)

    # return res.set_index(['Country', 'Date']).astype('float64')

def get_mexico_data(verbose = False):
    base_url = "https://raw.githubusercontent.com/mariorz/covid19-mx-time-series/master/data/covid19_{}_mx.csv"
    types = [('confirmed', 'Confirmed'),
             ('deaths', 'Deaths'),
             ('negatives', 'Negatives')]
    base_df = pd.DataFrame()

    for url_name, my_name in types:
        if verbose: print('Retrieving Mexico {}'.format(url_name))
        df = pd.read_csv(base_url.format(url_name))
        df = df.drop(columns = ['Estado']).sum(axis=0).rename_axis('Date').rename(my_name).to_frame()
        base_df = base_df.join(df, how = 'outer')

    base_df['TotalTests'] = base_df['Confirmed'] + base_df['Negatives']
    base_df['Country'] = ['Mexico'] * len(base_df.index)

    base_df = base_df.drop(columns = 'Negatives')

    base_df = base_df.replace(0, np.nan).reset_index().set_index(['Country', 'Date'])

    return base_df

def clean_chile_data(df, df_name):
    if df_name == 'TotalesNacionales':
        rename_map = {
            'Casos totales': 'Confirmed',
            'Casos recuperados': 'Recovered',
            'Fallecidos': 'Deaths'
        }
        df = df.T
        df.columns = df.iloc[0].str.rstrip()
        df = df[1:].rename(columns = rename_map)[list(rename_map.values())]
    elif df_name == 'PCREstablecimiento':
        df = df.query('Examenes == "realizados"').T
        df = df[2:].astype('int64').sum(axis=1).rename('TotalTests').to_frame()
    elif df_name == 'UCI':
        df = df.T.drop(['Region', 'Codigo region', 'Poblacion']).sum(axis=1).rename('ICU').to_frame()
    elif df_name == 'HospitalizadosEtario':
        df.T.drop(['Grupo de edad', 'Sexo']).astype('int64').sum(axis=1).rename('Hospitalized').to_frame()

    return df

def get_chile_data(verbose = False):
    prod_filename_map = {
        5: 'TotalesNacionales',
        8: 'UCI',
        17: 'PCREstablecimiento',
    }
    general_URL_form = 'https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto{}/{}.csv'

    master_df = pd.DataFrame()

    for num, name in prod_filename_map.items():
        url = general_URL_form.format(num, name)
        if verbose: print("Retrieving Chile {}".format(name))
        df = pd.read_csv(url)

        df = clean_chile_data(df, name)

        master_df = master_df.join(df, how = 'outer')

    master_df['Country'] = ['Chile'] * len(master_df.index)
    master_df.index = master_df.index.rename('Date')

    return master_df.reset_index().set_index(['Country', 'Date']).astype('float64').replace(0, np.NaN)

def get_panama_data(verbose = False):
    if verbose: print("Retrieving Panama data")
    df = pd.read_csv('https://raw.githubusercontent.com/c0t088/DAP-Panama/master/data_covid_pma_dia.csv')

    fields_relevant = {
        'Fecha': 'Date',
        'Casos_confirmados': 'Confirmed',
        'Fallecidos_tot': 'Deaths',
        'Domicilio': 'Home',
        'Hosp_sala': 'Hospitalized',
        'Hosp_uci': 'ICU',
        'Recuperados': 'Recovered',
        'Pruebas negativas': 'NegTests',
        'Pruebas positivas': 'PosTests'
        }

    total_tests = df[['Fecha', 'Pruebas negativas', 'Pruebas positivas']].set_index('Fecha').cumsum().sum(axis=1).rename('TotalTests')

    df = df[list(fields_relevant.keys())]

    df.columns = [fields_relevant.get(c, c) for c in df.columns]
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date')

    df = df.join(total_tests).drop(columns = ['NegTests', 'PosTests'])
    df['Hospitalized'] = df['Hospitalized'] + df['ICU']
    df['Country'] = ['Panama'] * len(df.index)

    return df.reset_index().set_index(['Country', 'Date'])

def join_dfs(default, other):
    #For joining dataframes, using one as default and filling in missing data
    overlap = set(default.columns).intersection(set(other.columns))
    default = pd.merge(default, other, left_index=True, right_index = True, how = 'outer', suffixes = ('', '_other'))
    for col in overlap:
        default[col] = default[col].combine_first(default[col + '_other'])

    default = default.drop([col + '_other' for col in overlap], axis=1)

    return default

def get_pop_dict():
    pop = pd.read_csv('data/WPP2019_TotalPopulationBySex.csv')
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

def merge_pop(df, verbose = False):
    if verbose: print("Retrieving population data.")
    pop = get_pop_dict()
    df = df.merge(pop, how = 'left', left_on = 'Country', right_index = True)
    return df

def data_clean(out_file, hard_refresh = False, verbose = False):

    dat = pd.read_csv('data/Covid19_Data.csv', index_col = 0)
    dat.index = pd.to_datetime(dat.index)

    col = dat.columns.str.split('_', expand=True)
    dat.columns = col
    dat.index = dat.index.rename("Date")
    dat.columns = dat.columns.rename(['Country', 'Col'])
    dat = dat.stack(level=0)
    dat.index = dat.index.reorder_levels(['Country', 'Date'])

    #Join the dataframes, add US, Italy, Mexico, Chile, Panama data from source.
    dat = join_dfs(dat, get_us_data(verbose = verbose))
    dat = join_dfs(dat, get_italy_data(verbose = verbose))
    dat = join_dfs(dat, get_mexico_data(verbose = verbose))
    dat = join_dfs(dat, get_chile_data(verbose = verbose))
    dat = join_dfs(dat, get_panama_data(verbose = verbose))

    #Get Hopkins data
    jhu_df = get_JHU_data('confirmed', verbose = verbose)
    jhu_death_df = get_JHU_data('deaths', verbose = verbose)
    jhu_df = jhu_death_df.join(jhu_df)
    jhu_death_df = None
    jhu_recovered_df = get_JHU_data('recovered', verbose = verbose)
    jhu_df = jhu_df.join(jhu_recovered_df)
    jhu_recovered_df = None
    dat = join_dfs(dat, jhu_df)


    jhu_df = None
    dat = merge_pop(dat, verbose = verbose)

    # if not hard_refresh:
    #     if verbose: print("Joining previously compiled data")
    #     old = pickle.load(open('data/compiled_data.p', 'rb')).reset_index()
    #     old.Date = pd.to_datetime(old.Date)
    #     old = old.set_index(['Country', 'Date'])
    #     dat = join_dfs(old, dat)

    #Tens of thousands of population
    dat['Pop10k'] = dat['Population'] / 10000

    #Add New Cases, New Tests
    dat['NewCases'] = dat.groupby('Country')['Confirmed'].diff()
    dat['NewTests'] = dat.groupby('Country')['TotalTests'].diff()
    dat['NewDeaths'] = dat.groupby('Country')['Deaths'].diff()
    dat['DaysSinceFirst'] = (dat['Confirmed'] >= 1).groupby('Country').cumsum().replace(0, np.nan) - 1
    dat['ConfirmedGrowth'] = dat.groupby('Country')['Confirmed'].pct_change() * 100.
    dat['DaysSinceTenthDeath'] = (dat['Deaths'] >= 10).groupby('Country').cumsum().replace(0, np.nan)
    dat['ActiveCases'] = dat['Confirmed'] - dat['Recovered']

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
        dat.loc[s, 'DaysSinceShutdown'] = new

    #Keep the ones with more than 1 confirmed day
    dat = dat[dat['Confirmed'] >= 1]

    #Set the index
    dat = dat.set_index([dat.index, "DaysSinceFirst", "DaysSinceTenthDeath", "DaysSinceShutdown"
                        ]).reorder_levels(["Country", "DaysSinceFirst", "DaysSinceTenthDeath", "DaysSinceShutdown",
                                        "Date"]).sort_index()
    #Pickle object, return success
    pickle.dump(dat, open(out_file, 'wb'))

    return dat

# sched = BackgroundScheduler()

# @sched.scheduled_job('cron', day_of_week='mon-sun',  hour = 23)
# def scheduled_job():
#     data_clean('compiled_data.p')

if __name__ == "__main__":
    # sched.start()
    data_clean('data/compiled_data.p', hard_refresh = True, verbose=True)