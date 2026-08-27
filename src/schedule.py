import matplotlib.pyplot as plt
import pandas as pd
import datetime
import sys

from src import *

import astroplan
from astroplan import Observer, FixedTarget
from astroplan import ObservingBlock

from astroplan.plots import plot_altitude, plot_airmass, plot_schedule_airmass
from astroplan.constraints import AtNightConstraint, AirmassConstraint, TimeConstraint, AltitudeConstraint, LocalTimeConstraint
from astroplan.scheduling import Transitioner, PriorityScheduler, Schedule

from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as u

"""
WIP very preliminary!
Builds schedule from input data
"""

# This currently assumes lower values of ``tagpriority`` is higher priority
# TODO: add tagadj overwriting tagpriority
def construct_blocks(fname, exposure_time, read_out_time):

    df = load_csv(fname, remove_zeros=True)
    
    blocks = []
    for index, row in df.iterrows():
        # Define variables we need from the dataframe 
        tagpriority = row['tagpriority']
        instrument = row['instrument']
        target = row['target']
        ra = row['ra2000']
        dec = row['dec2000']
        n_scans = row['remaining']

        # Construct target object
        target = FixedTarget(coord=SkyCoord(ra=ra*u.deg, dec=dec*u.deg), name=target)

        # Construct observing block objects, split each scan into singular block
        if n_scans > 1:
            for n in range(n_scans):
                b = ObservingBlock.from_exposures(target, tagpriority, exposure_time, 1, read_out_time,
                                                  configuration = {"Instrument": instrument})
                blocks.append(b)     
        else:
            b = ObservingBlock.from_exposures(target, tagpriority, exposure_time, 1, read_out_time,
                                          configuration = {"Instrument": instrument})
            blocks.append(b)

    return blocks 

# Not pretty, but it tells you if you're missing observations
def check_schedule(config):

    df_data = load_csv(config['data']['path'], remove_zeros=True)

    start_date = config['observations']['start_date'].split(" ")[0]
    end_date = config['observations']['end_date'].split(" ")[0]
    fin = f"./data_out/{start_date}_{end_date}_schedule.csv" 

    df_schedule = pd.read_csv(fin, sep=',')
    df_schedule = df_schedule[df_schedule['target'] != "TransitionBlock"]
    df_schedule = df_schedule.reset_index(drop=True)

    # Returns a dictonary with the total number of scans planned per target.
    planned_targets = {}
    for index, row in df_data.iterrows():
        if row['target'] not in planned_targets:
            planned_targets[row['target']] = row['remaining']
        else:
            planned_targets[row['target']] += row['remaining']

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
        df_missing.to_csv(f"./data_out/{start_date}_{end_date}missing_targets.csv", index=False) 
    else:
        print("All targets in schedule!")

# TODO: add more constraint options
def collect_global_constraints(config):

    constraint_list = []
    # Altitude constraint
    if config['global_constraints']['altitude']['bool']:
        min_altitude = config['global_constraints']['altitude']['min_altitude']
        max_altitude = config['global_constraints']['altitude']['max_altitude']
        constraint_list.append(AltitudeConstraint(min=min_altitude*u.degree, max=max_altitude*u.degree))

    # Airmass constraint
    if config['global_constraints']['airmass']['bool']:
        min_airmass = config['global_constraints']['airmass']['min_airmass']
        max_airmass = config['global_constraints']['airmass']['max_airmass']
        boolean = config['global_constraints']['airmass']['boolean_constraint']
        constraint_list.append(AirmassConstraint(max=max_airmass, min=min_airmass, boolean_constraint=boolean))

    # Local time constraint
    if config['global_constraints']['local_time']['bool']:
        min_time = datetime.time(config['global_constraints']['local_time']['min_time'][0], 
                                 config['global_constraints']['local_time']['min_time'][1])
        max_time = datetime.time(config['global_constraints']['local_time']['max_time'][0],
                                 config['global_constraints']['local_time']['max_time'][1])
        constraint_list.append(LocalTimeConstraint(min=min_time, max=max_time))

    # At night constrain
    if config['global_constraints']['at_night']['bool']:
        astronomical = config['global_constraints']['at_night']['twilight_astronomical']
        civil = config['global_constraints']['at_night']['twilight_civil']
        nautical = config['global_constraints']['at_night']['twilight_nautical']

        if astronomical == True & civil == False & nautical == False:
            constraint_list.append(AtNightConstraint.twilight_astronomical())
        elif astronomical == False & civil == True & nautical == False:
            constraint_list.append(AtNightConstraint.twilight_civil())
        elif astronomical == False & civil == False & nautical == True:
            constraint_list.append(AtNightConstraint.twilight_nautical())
        else:
            sys.exit("Only one of astronomoical, civil, or nautical can be true. Quitting...")
   
    return constraint_list

# TODO: Improve plotting 
def schedule(fname):

    ## Load Config File ##
    config = load_config(fname)

    ## Observatory ##
    observer = Observer.at_site(config['telescope']['observatory'])

    ## Start and End dates ##
    start_time = Time(config['observations']['start_date'], format='iso')
    end_time = Time(config['observations']['end_date'], format='iso')

    ## Global Constraints ##
    global_constraints = collect_global_constraints(config)

    ## Exposure times ##
    exp_time = config['observations']['exp_time'] * u.second
    read_out = config['telescope']['read_out'] * u.second

    ## Observing Blocks ##
    blocks = construct_blocks(config['data']['path'], exp_time, read_out)

    ## Transitioner ##
    # Takes about ~20 minutes for the new instrument to be ready
    slew_rate = config['telescope']['read_out'] * u.deg/u.second
    transitioner = Transitioner(slew_rate, {'Instrument': {('UU', 'AWEOWEO'): 1200*u.second,
                                                           ('UU', 'KUNTUR'): 1200*u.second,
                                                           ('AWEOWEO', 'KUNTUR'): 1200*u.second,
                                                            'default': 1200*u.second}})

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

    start_date = config['observations']['start_date'].split(" ")[0]
    end_date = config['observations']['end_date'].split(" ")[0]
    fout = f"./data_out/{start_date}_{end_date}_schedule.csv"   
    df_out.to_csv(fout, index=False)

    ## Check if all targets are in the schedule, save any that cannot be fit into the schedule
    check_schedule(config)

    ## Plot schedule
    plt.figure(figsize = (14,6))
    plot_schedule_airmass(priority_schedule)
    plt.legend(loc = "upper right")
    #plt.show()


if __name__ == "__main__":  

    # Check if arguments were actually passed
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        print("No arguments were provided.")

    schedule(config_path)