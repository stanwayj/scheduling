import pandas as pd
import numpy as np

# Add weatherband dictonary (from construct blocks) to schedule csv 
def add_weather_bands(df, weatherband_dict, fout):

    weatherband_list = []
    for index, row in df.iterrows():
        if row['target'] != "TransitionBlock":
            instrument = row['configuration'].split("'")[3]
            targetid = row['target']
            projectid, target = targetid.split("_")
        
            key = f'{projectid}_{instrument}_{target}'      
            weatherband_list.append(int(weatherband_dict[key]))
        else:
            weatherband_list.append(np.nan)

    df['weather band'] = weatherband_list
    df.to_csv(fout, index=False)