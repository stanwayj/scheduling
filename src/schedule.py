import matplotlib.pyplot as plt
import pandas as pd
import datetime
import sys

from src import *
from src.schedule_func.blocks import *
from src.schedule_func.check_schedule import *
from src.schedule_func.global_constraints import *
from src.schedule_func.weatherbands import *
from src.schedule_func.transition import *

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