from datetime import date, timedelta
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import sys, os

from src import *

from astropy.time import Time
import astropy.units as u

"""
Produces a vareity of plots for all scheduled observations
"""

# Remake/improve this when I add instruments to config file. 
def plot_histo_instrument(fname):

    df = load_csv(fname)

    # Seperate by instrument
    instrument_list = config['instruments']['instrument_list']
    histo_list = []
    for inst in instrument_list:
        histo_list.append(df[df.instrument == inst]['ra2000'])

    # Colourbar setup
    ninst = len(instrument_list)
    cmap = cm.viridis
    bounds = np.arange(ninst + 1)
    norm = mcolors.BoundaryNorm(bounds, cmap.N)
    colors = [cmap(i / (ninst - 1)) for i in range(ninst)]

    fig, ax = plt.subplots(1,1, figsize=(8,6))

    ax.hist(histo_list, bins=36, stacked=True, color=colors, label = instrument_list)

    ax.set_ylabel("Number of sources", fontsize=15)
    ax.set_xlabel(r"RA [$^\circ$]", fontsize=15)

    ax.set_xlim(0, 360)
    ax.set_xticks([0, 45, 90, 135, 180, 225, 270, 315, 360])
    
    fig.suptitle(r"Distribution of RA in $10^\circ$ increments" + "\n" + "Seperated by Instrument")

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)      
    cbar = fig.colorbar(sm, ax=ax, boundaries=bounds, ticks=bounds, pad=0.01)
    cbar.ax.set_yticks([i + 0.5 for i in range(ninst)])
    cbar.ax.set_yticklabels(instrument_list)

    plt.savefig("./plots/overview_histo_instrument.png", dpi=200, bbox_inches="tight")


def plot_histo_dec(fname):  

    df = load_csv(fname)

    # Seperate by DEC
    dec_range = [[-90, -60], [-60, -30], [-30, 0], [0, 30], [30, 60], [60, 90]]
    histo_list = []
    for i in range(len(dec_range)):
        df_dec = df[(df['dec2000'] > dec_range[i][0]) & (df['dec2000'] < dec_range[i][1])]
        histo_list.append(df_dec['ra2000'])

    # Colourbar setup
    bounds = [-90, -60, -30, 0, 30, 60 , 90]
    midpoints = [-75, -45, -15, 15, 45, 75]
    cmap = cm.viridis
    norm = mcolors.BoundaryNorm(boundaries=bounds, ncolors=cmap.N)
    colours = [cmap(norm(val)) for val in midpoints]

    fig, ax = plt.subplots(1,1, figsize=(8,6))

    ax.hist(histo_list, bins=36, stacked=True, color=colours) 

    ax.set_ylabel("Number of sources", fontsize=15)
    ax.set_xlabel(r"RA [$^\circ$]", fontsize=15)

    ax.set_xlim(0, 360)
    ax.set_xticks([0, 45, 90, 135, 180, 225, 270, 315, 360])

    fig.suptitle(r"Distribution of RA in $10^\circ$ increments" + "\n" + "Seperated by DEC")

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)      
    cbar = fig.colorbar(sm, ax=ax, boundaries=bounds, ticks=bounds, pad=0.01)
    cbar.ax.set_title(r"DEC [$^\circ$]", y=1.01)

    plt.savefig("./plots/overview_histo_ra.png", dpi=200, bbox_inches="tight")   


def plot_histo_schedule(config, weatherband, instrument):

    df_schedule = load_schedule(config, weatherband, instrument)
    start_time = config['observations']['start_time']

    observing_time_per_night = {}
    for index, row in df_schedule.iterrows():
        date, time = row['start time (UTC)'].split(" ")
        yesterday = (Time(date) - 1 * u.day).iso.split(" ")[0]

        # Check if any observations for that date in the dictonary
        if date not in observing_time_per_night:
            # Make a new entry if the time is after the start of observations
            if Time(date + " " + time.split(".")[0]) >= Time(date + " " + start_time):
                observing_time_per_night[date] = row['duration (minutes)'] / 60
            # If not its from the previous night
            else:
                # Check if any observations exist from the previous night
                if yesterday not in observing_time_per_night:
                    # If yes, make a new entry
                    observing_time_per_night[yesterday] = row['duration (minutes)'] / 60
                else:
                    # If no, add time to previous entry
                    observing_time_per_night[yesterday] += row['duration (minutes)'] / 60
        # Observations from this day already exist in the directory
        else:
            # Append duration to previous total if the time is after the start of observations
            if Time(date + " " + time.split(".")[0]) >= Time(date + " " + start_time):
                observing_time_per_night[date] += row['duration (minutes)'] / 60
            # If not, once again we check the previous night.
            else:
                if yesterday not in observing_time_per_night:
                    observing_time_per_night[yesterday] = row['duration (minutes)'] / 60
                else:
                    observing_time_per_night[yesterday] += row['duration (minutes)'] / 60         

    # Add dates with no observations to dictonary for plotting
    start_date = config['observations']['start_date']
    end_date = config['observations']['end_date']
    date_range = pd.date_range(start=start_date, end=end_date).strftime('%Y-%m-%d')
    dates_list = date_range.tolist()
    for date in dates_list:
        if date not in observing_time_per_night:
            observing_time_per_night[date] = 0

    # Add the day before and after to pad plot
    day_before = (Time(start_date) - 1 * u.day).iso.split(" ")[0]
    day_after = (Time(end_date) + 1 * u.day).iso.split(" ")[0]
    observing_time_per_night[day_before] = 0
    observing_time_per_night[day_after] = 0
    
    # Reorder dictionary
    observations_order = {key: observing_time_per_night[key] for key in sorted(observing_time_per_night)}

    # Plotting functions
    fig, ax = plt.subplots(1,1, figsize=(7,2.5))

    dates = observations_order.keys()
    hours = list(observations_order.values())

    norm = mcolors.Normalize(vmin=0, vmax=12)
    colors = cm.jet(norm(hours))

    ax.bar(dates, hours, color=colors, edgecolor='k', linewidth=0.5, width=1)

    ax.set_xlabel("Dates", fontsize=12)
    ax.set_ylabel("Hours per night", fontsize=12)

    ax.set_ylim(0, 12)
    ax.set_xlim(config['observations']['start_date'], config['observations']['end_date'])

    sm = cm.ScalarMappable(cmap='jet', norm=norm)
    sm.set_array([]) 
    cbar = fig.colorbar(sm, ax=ax, pad=0.01)

    # Title
    missing_targets = f"./data_out/{start_date}_{end_date}_missing_targets.csv"
    if os.path.isfile(missing_targets):
        ax.set_title(f"Weatherband={weatherband} - Instrument={instrument}" + '\n' 
                     "Not all targets in schedule!" + "\n" + 
                     f"Check data_out/{start_date}_{end_date}_missing_targets.csv for details")
    else:
        ax.set_title(f"Weatherband={weatherband} - Instrument={instrument}" + '\n' 
                     "All targets in schedule!")

    # Logic (ish) for x tick labels
    nmonths = int(end_date.split("-")[1]) - int(start_date.split("-")[1])
    if nmonths < 0:
        nmonths += 12

    xlabel_list = [start_date]
    for n in range(nmonths):
        start_month = int(start_date.split("-")[1]) + 1
        year = int(start_date.split("-")[0])
        month = start_month + n

        if month > 12:
            year += 1
            month -= 12
        if month < 10:
            xlabel_list.append(f'{year}-0{month}-01')
        else:
            xlabel_list.append(f'{year}-{month}-01')

    xlabel_list.append(end_date)
    ax.set_xticks(xlabel_list)
    plt.xticks(rotation=90)

    # Add weatherband/instrument to filename
    if isinstance(weatherband, int) or instrument != 'All':
        fout = f"./plots/verbose/hours_per_night_weatherband={weatherband}_instrument={instrument}.png"
    else:
        fout = "./plots/hours_per_night_all_observations.png"

    plt.savefig(fout, dpi=200, bbox_inches="tight")
    plt.close()

if __name__ == "__main__":  

    # Check if arguments were actually passed
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        print("No arguments were provided.")

    config = load_config(config_path)

    plot_histo_instrument(config['data']['path'])
    #plot_histo_dec(config['data']['path'])

    # Make plots for all weatherbands and instruments
    #inst_list = config['instruments']['instrument_list'] + ['All']
    #for wb in [1, 2, 3, 4, 5, 'All']:
    #    for inst in inst_list:
    #        plot_histo_schedule(config, weatherband=wb, instrument=inst)