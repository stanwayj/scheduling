import matplotlib.pyplot as plt
import pandas as pd
import datetime

from src import load_csv

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

        # Construct observing block objects
        b = ObservingBlock.from_exposures(target, tagpriority, exposure_time, n_scans, read_out_time,
                                          configuration = {"Instrument": instrument})
        blocks.append(b)
        
    return blocks   


# TODO: Dates, constraints, and exposure (maybe more) times should be read from a parameter file 
def schedule(fname, start, end, site='jcmt'):

    ## Observatory ##
    observer = Observer.at_site(site)

    ## Start and End dates ##
    start_time = Time(start, format='iso')
    end_time = Time(end, format='iso')

    ## Global Constraints ##
    # TODO: add options for more/less constraints from parameter file
    global_constraints = [AltitudeConstraint(min=30*u.degree, max=85*u.degree),
                          AirmassConstraint(max = 3, boolean_constraint = False),
                          LocalTimeConstraint(min=datetime.time(00,00), max=datetime.time(12,00))]

    ## Exposure times ##
    exp_time = 60 * u.second
    read_out = 20 * u.second

    # Call blocks from function
    blocks = construct_blocks(fname, exp_time, read_out)

    ## Transitioner ##
    # Takes about ~20 minutes for the new instrument to be ready
    slew_rate = 0.8*u.deg/u.second
    transitioner = Transitioner(slew_rate, {'Instrument': {('UU', 'AWEOWEO'): 1200*u.second,
                                                           ('UU', 'KUNTUR'): 1200*u.second,
                                                           ('AWEOWEO', 'KUNTUR'): 1200*u.second,
                                                            'default': 1200*u.second}})

    ## Priority Scheduler ##
    prior_scheduler = PriorityScheduler(constraints = global_constraints,
                                        observer = observer,
                                        transitioner = transitioner)

    priority_schedule = Schedule(start_time, end_time)
    prior_scheduler(blocks, priority_schedule)

    # Convert to Pandas Dataframe and save as csv
    df_out = priority_schedule.to_table().to_pandas()
    df_out.to_csv("./data_out/schedule.csv", index=False)

    ######### Plot schedule
    plt.figure(figsize = (14,6))
    plot_schedule_airmass(priority_schedule)
    plt.legend(loc = "upper right")
    plt.show()

schedule("./data_in/26BPI-remainingobservations.csv", '2026-08-06 19:00', '2026-08-10 19:00')
 