import pandas as pd
import sys

from src import *
from src.schedule_func.blocks import *
from src.schedule_func.check_schedule import *
from src.schedule_func.global_constraints import *
from src.schedule_func.weatherbands import *
from src.schedule_func.transition import *
from src.schedule_func.construct_schedule import *

"""
WIP somewhat preliminary!
Builds schedule from input data
"""

# TODO: Break schedule into smaller blocks (e.g. week long) to reduce RAM usage
def schedule(config):

    ## Global Constraints ##
    global_constraints = collect_global_constraints(config)

    ## Construct Observing Blocks ##
    blocks, weatherband = construct_blocks(config)

    ## Construct Transitioner ##
    transitioner = construct_transitioner(config)

    ## Construct schedule and return as a Dataframe ##
    df_out = construct_schedule(config, global_constraints, transitioner, blocks)

    ## Save schedule ## 
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