from astroplan import Observer, FixedTarget

from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as u

"""
Determine the rise and set time of the target given RA and DEC for a given date.

Target is assumed to be observable if it is 30 degrees above the horizon.
"""

def rise_and_set_times(ra, dec, date, site='JCMT'):

    # supports facilities in astropy database
    facility = Observer.at_site(site)

    # construct target via SkyCoord object
    target_coords = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
    target = FixedTarget(coord=target_coords)

    # construct time object
    time = Time(date, scale="utc", format="iso")

    # Find rise and set time of the target
    rise_time = facility.target_rise_time(time, target, which='next', horizon=30*u.deg)
    set_time = facility.target_set_time(time, target, which='next', horizon=30*u.deg)

    # ensure rise and set times correspond to the same observation
    delta = set_time - rise_time
    if delta.sec / 3600 > 12:
        set_time = facility.target_set_time(time, target, which='nearest', horizon=30*u.deg)
    elif delta.sec / 3600 < 0:
        rise_time = facility.target_rise_time(time, target, which='nearest', horizon=30*u.deg)
  
    return rise_time.iso, set_time.iso
