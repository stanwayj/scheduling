import astroplan
from astroplan import Observer

from astroplan.scheduling import PriorityScheduler, Schedule

from astropy.time import Time
import astropy.units as u


def construct_schedule(config, constraints, transitioner, blocks):

    ## Observatory ##
    observer = Observer.at_site(config['telescope']['observatory'])

    ## Start and End dates ##
    start_time = Time(config['observations']['start_date'] + " " + config['observations']['start_time'], format='iso')
    end_time = Time(config['observations']['end_date'] + " " + config['observations']['end_time'], format='iso')

    ## Time resolution of schedule ##
    time_resolution = config['misc']['time_resolution'] * u.second

    ## Initialise schedule with constraints and transition ##
    prior_scheduler = PriorityScheduler(constraints = constraints,
                                        observer = observer,
                                        transitioner = transitioner,
                                        time_resolution = time_resolution)

    ## Schedule the observing blocks ##
    priority_schedule = Schedule(start_time, end_time)
    prior_scheduler(blocks, priority_schedule)

    ## Convert schedule to Dataframe and return to central script ##
    df = priority_schedule.to_table().to_pandas()
    return df