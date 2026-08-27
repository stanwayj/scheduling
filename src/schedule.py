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

def check_schedule(config):

    df_data = load_csv(config['data']['path'], remove_zeros=True)
    df_schedule = pd.read_csv("./data_out/schedule.csv", sep=',')
    df_schedule = df_schedule[df_schedule['target'] != "TransitionBlock"]
    df_schedule = df_schedule.reset_index(drop=True)

    if df_data.shape[0] != df_schedule.shape[0]:
        print("Targets Missing! Saving list of missing targets to csv...")

        planned_targets = df_data[['target']]
        scheduled_targets = df_schedule[['target']]

        merged = df_data.merge(df_schedule, on='target', how='outer', indicator=True)
        missing_targets = merged[merged['_merge'] == 'left_only']
        missing_targets = missing_targets.drop(columns=['_merge', 'start time (UTC)', 'end time (UTC)', 
                                                        'duration (minutes)', 'ra', 'dec', 'configuration'])

        missing_targets.to_csv("./data_out/missing_targets.csv", index=False)
        
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
    df_out.to_csv("./data_out/schedule.csv", index=False)

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