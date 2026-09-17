import pandas as pd
import warnings

from ..io import *

# Not pretty, but it tells you if you're missing observations
def check_schedule(config):

    df_data = load_csv(config, remove_zeros=True)

    start_date = config['observations']['start_date']
    end_date = config['observations']['end_date']
    fin = f"./data_out/{start_date}_{end_date}_schedule.csv" 
    df_schedule = load_schedule(config)
    
    # Raise warning is weatherband has not been saved to the schedule
    if 'weather band' not in df_schedule.columns:
        warnings.warn("Weather band not added to schedule but exists in input data.")

    # Returns a dictonary with the total number of scans planned per target.
    planned_targets = {}
    for index, row in df_data.iterrows():
        if row['target'] not in planned_targets:
            planned_targets[row['projectid'] + "_" + row['target']] = row['remaining']
        else:
            planned_targets[row['projectid'] + "_" + row['target']] += row['remaining']

    # Returns a dictonary with the total number of scans scheduled per target.
    scheduled_targets = {}
    for index, row in df_schedule.iterrows():
        if row['target'] not in scheduled_targets:
            scheduled_targets[row['target']] = 1
        else:
            scheduled_targets[row['target']] += 1 
    
    # Create a new DataFrame of missed targets
    df_missing = pd.DataFrame(columns=['target', 'instrument', 'ra2000', 'dec2000', 'remaining'])
    for key, value in planned_targets.items():
        # Some targets may have some, but not all of the scheduled observations.
        try:
            diff = value - scheduled_targets[key]
            if diff > 0:
                
                target_info = df_data.loc[df_data['target'] == key, ['instrument', 'ra2000', 'dec2000']]
                target_info = target_info.iloc[0]
                new_row = {'target':key, 'instrument':target_info['instrument'], 'ra2000':target_info['ra2000'],
                        'dec2000':target_info['dec2000'], 'remaining':diff}
                df_missing = pd.concat([df_missing, pd.DataFrame([new_row])], ignore_index=True)
        # Some may not be observed at all.     
        except:
            target_info = df_data.loc[df_data['target'] == key, ['instrument', 'ra2000', 'dec2000', 'remaining']]
            remaining = target_info['remaining'].sum() 
            new_row = {'target':key, 'instrument':target_info['instrument'], 'ra2000':target_info['ra2000'],
                       'dec2000':target_info['dec2000'], 'remaining':remaining} 
            df_missing = pd.concat([df_missing, pd.DataFrame(new_row)], ignore_index=True)
            continue

    # Save the missing targets to a file if any are missed.  
    if df_missing.shape[0] > 0:
        print("Targets Missing! Saving list of missing targets to csv...")
        df_missing.to_csv(f"./data_out/{start_date}_{end_date}_missing_targets.csv", index=False) 
    else:
        print("All targets in schedule!")