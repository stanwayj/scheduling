import datetime

import astroplan
from astroplan.constraints import AtNightConstraint, AirmassConstraint, AltitudeConstraint, LocalTimeConstraint

import astropy.units as u

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
