import astroplan
from astroplan.scheduling import Transitioner

import astropy.units as u

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