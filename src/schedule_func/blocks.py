import pandas as pd

import astroplan
from astroplan import FixedTarget, ObservingBlock

from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as u

from ..io import *

# Construct observing blocks for each observation in the schedule
def construct_blocks(config):
    
    df = load_csv(config, remove_zeros=True)
    read_out_time = config['telescope']['read_out'] * u.second

    blocks = []
    weatherband = {}
    for index, row in df.iterrows():
        # Define variables we need from the dataframe 
        tagpriority = row['tagpriority']
        instrument = row['instrument']
        targetid = row['target']
        ra = row['ra2000']
        dec = row['dec2000']
        n_scans = row['remaining']
        projectid = row['projectid']
        
        # Find exposure time from input data, or default value from config file
        if 'exposure time' in df.columns:
            exposure_time = row['exposure time'] * 60 * u.second
            
        elif isinstance(config['observations']['exp_time'], int):
            exposure_time = config['observations']['exp_time'] * u.second
        else:
            raise TypeError("Cannot find exposure time! Add to input data or set a default value in configuration.yaml")  

        # Override priority if `tagadj` has been set
        if 'tagadj' in df.columns and row['tagadj'] > 0:
            priority = row['tagadj']
        else:
            priority = tagpriority

        # Construct target object
        block_name = f'{projectid}_{targetid}'
        target = FixedTarget(coord=SkyCoord(ra=ra*u.deg, dec=dec*u.deg), name=block_name)

        # Construct observing block objects, split each scan into singular block
        if n_scans > 1:
            for n in range(n_scans):
                b = ObservingBlock.from_exposures(target, priority, exposure_time, 1, read_out_time,
                                                  configuration = {"Instrument": instrument})
                blocks.append(b)     
        else:
            b = ObservingBlock.from_exposures(target, priority, exposure_time, 1, read_out_time,
                                              configuration = {"Instrument": instrument})
            blocks.append(b)

        # Weatherband dictionary entry
        key = f'{projectid}_{instrument}_{targetid}'
        weatherband[key] = row['weatherband']

    return blocks, weatherband 