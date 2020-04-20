from sodapy import Socrata
import pandas as pd
import numpy as np
import datetime

def load_from_col(api_key):
    client = Socrata("datos.gov.co",
                    api_key,
                    )

    results = client.get("gt2j-8ykr", limit = 100000)

    results = pd.DataFrame.from_records(results)
    return results

def clean_data(results):
    #Cleans the data loaded from the Colombia API

    #Filter out babies that have ages in months
    results = results[~results.edad.str.contains('mes', na= True)]

    new_map = {
        'fecha_de_diagn_stico': 'fecha_de_diagnostico',
        'ciudad_de_ubicaci_n' : 'ciudad_de_ubicacion',
        'atenci_n': 'atencion',
        'pa_s_de_procedencia': ' pais_de_procedencia'
    }
    results = results.rename(columns = new_map)
    results.fecha_de_diagnostico = pd.to_datetime(results.fecha_de_diagnostico)
    results.fecha_recuperado = results.fecha_recuperado.replace({'No': np.nan})
    results.fecha_recuperado = pd.to_datetime(results.fecha_recuperado)
    results.fis = results.fis.replace(['Asintomático', 'No disponible'], np.nan)
    results.fis = pd.to_datetime(results.fis)
    results.fecha_de_muerte = pd.to_datetime(results.fecha_de_muerte)

    results.id_de_caso = results.id_de_caso.astype('int32')
    results.edad = results.edad.astype('int32')

    results = results.set_index("id_de_caso")

    results = results.rename(columns = {'atencion': datetime.date.today()})

    results.to_csv('Colombia_data.csv')

    return results

def mixs(x):
    try:
        x_date = pd.to_datetime(x)
        return (1, x_date, '')
    except:
        return (0, x, '')

def refresh_data():
    with open('col_api_key.txt') as f:
        api_key = f.readline().rstrip()

    results = load_from_col(api_key)

    results = clean_data(results)

    # print(results.columns)
    """
    Need to
        0) load old dataframe CSV
        1) join on the static columns (outer join so that we keep new datapoints) -
        2) Add the date column along with 'state' -
        3) Update columns that may be missing data (such as fecha recuperado, fecha muerte, fis) - combine first
        4) write to CSV
    """
    old = pd.read_csv('Colombia_data.csv', index_col = 0, parse_dates = True)

    old = old.combine_first(results)
    old = old.reindex(sorted(old.columns, key = mixs), axis=1)

    old.to_csv('Colombia_data.csv')

    return results


if __name__ == "__main__":
    refresh_data()