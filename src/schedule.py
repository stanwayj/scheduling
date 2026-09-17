import matplotlib.pyplot as plt
import pandas as pd
import datetime
import sys

from src import *
from src.schedule_func.blocks import *
from src.schedule_func.check_schedule import *
from src.schedule_func.global_constraints import *

import astroplan
from astroplan import Observer

from astroplan.constraints import AtNightConstraint, AirmassConstraint, TimeConstraint, AltitudeConstraint, LocalTimeConstraint
from astroplan.scheduling import Transitioner, PriorityScheduler, Schedule

from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as u

"""
WIP somewhat preliminary!
Builds schedule from input data
"""

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

# Add transition between instruments from config file
def construct_transitioner(config):

    instrument_list = config['instruments']['instrument_list']
    instrument_dict = {}
    for inst in instrument_list:
        key = [f'{inst}_to_{swap}' for swap in instrument_list if swap != inst]
        
        for i in range(len(key)):
            try:
                a, b = key[i].split('_to_')
                instrument_dict[(a, b)] = config['instruments']['transitions'][key[i]] * u.second
            except:
                pass

    # Add default swap time as a fall back
    instrument_dict['default'] = config['instruments']['transitions']['default'] * u.second

    slew_rate = config['telescope']['read_out'] * u.deg/u.second
    transitioner = Transitioner(slew_rate, {'Instrument': instrument_dict})
    
    return transitioner

# TODO: Break schedule into smaller blocks (e.g. week long) to reduce RAM usage
def schedule(config):

    ## Observatory ##
    observer = Observer.at_site(config['telescope']['observatory'])

    ## Start and End dates ##
    start_time = Time(config['observations']['start_date'] + " " + config['observations']['start_time'], format='iso')
    end_time = Time(config['observations']['end_date'] + " " + config['observations']['end_time'], format='iso')

    ## Global Constraints ##
    global_constraints = collect_global_constraints(config)

    ## Construct Observing Blocks ##
    blocks, weatherband = construct_blocks(config)

    ## Construct Transitioner ##
    transitioner = construct_transitioner(config)

    ## Priority Scheduler ##
    time_resolution = config['misc']['time_resolution'] * u.second
    prior_scheduler = PriorityScheduler(constraints = global_constraints,
                                        observer = observer,
                                        transitioner = transitioner,
                                        time_resolution = time_resolution)

    priority_schedule = Schedule(start_time, end_time)
    prior_scheduler(blocks, priority_schedule)

    ## Convert to Pandas Dataframe and save as csv
    df_out = priority_schedule.to_table().to_pandas()

    start_date = config['observations']['start_date']
    end_date = config['observations']['end_date']
    fout = f"./data_out/{start_date}_{end_date}_schedule.csv"   
    df_out.to_csv(fout, index=False)

    ## Add weather band information to schedule csv and override original
    schedule = load_schedule(config, drop_transition=False)
    add_weather_bands(schedule, weatherband, fout)

    ## Check if all targets are in the schedule, save any that cannot be fit into the schedule
    check_schedule(config)


if __name__ == "__main__":  

    # Check if arguments were actually passed
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        print("No arguments were provided.")

    config = load_config(config_path)

    schedule(config)
    #construct_blocks(config)