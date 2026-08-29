from datetime import date, timedelta
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import sys

from src import *

from astropy.time import Time
import astropy.units as u

"""
Produces a vareity of plots for all scheduled observations
"""


def plot_histo_instrument(fname):

    df = load_csv(fname)

    ra_UU = df[df.instrument == "UU"]
    ra_KUNTUR = df[df.instrument == "KUNTUR"]
    ra_AWEOWEO = df[df.instrument == "AWEOWEO"]

    fig, ax = plt.subplots(1,1, figsize=(8,6))

    ax.hist([ra_UU['ra2000'], ra_KUNTUR['ra2000'], ra_AWEOWEO['ra2000']], bins=36, stacked=True, 
            color=['crimson', 'navy', 'dodgerblue'], label = ['UU', 'KUNTUR', 'AWEOWEO'])

    ax.set_ylabel("Count")
    ax.set_xlabel("RA [degrees]")

    ax.set_xlim(0, 360)
    fig.suptitle(r"Distribution of RA in $10^\circ$ increments" + "\n" + "Seperated by Instrument")

    ax.legend()

    plt.savefig("./plots/overview_histo_instrument.png", dpi=200)


def plot_histo_dec(fname):  

    df = load_csv(fname)

    dec_range = [[-90, -60], [-60, -30], [-30, 0], [0, 30], [30, 60], [60, 90]]
    histo_list = []
    for i in range(len(dec_range)):
        df_dec = df[(df['dec2000'] > dec_range[i][0]) & (df['dec2000'] < dec_range[i][1])]
        histo_list.append(df_dec['ra2000'])


    color_list = ["#0000ff", "#3300cc", "#660099", "#990066", "#cc0033", "#ff0000"]
    label_list = [r"$-90^\circ < DEC < -60^\circ$", r"$-60^\circ < DEC < -30^\circ$", 
                  r"$-30^\circ < DEC < 0^\circ$", r"$0^\circ < DEC < 30^\circ$", 
                  r"$30^\circ < DEC < 60^\circ$", r"$60^\circ < DEC < 90^\circ$"]

    fig, ax = plt.subplots(1,1, figsize=(8,6))

    ax.hist(histo_list, bins=36, stacked=True, color=color_list, label=label_list) 

    ax.set_ylabel("Count")
    ax.set_xlabel("RA [degrees]")

    ax.set_xlim(0, 360)
    fig.suptitle(r"Distribution of RA in $10^\circ$ increments" + "\n" + "Seperated by DEC")

    ax.legend(loc="upper center", ncols=2)

    plt.savefig("./plots/overview_histo_ra.png", dpi=200)   


def plot_histo_schedule(config):

    df_schedule = load_schedule(config)
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

    print(observations_order)
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
    ax.set_xticklabels([])

    sm = cm.ScalarMappable(cmap='jet', norm=norm)
    sm.set_array([]) 
    cbar = fig.colorbar(sm, ax=ax)

    plt.savefig("./plots/overview_hours_per_night.png", dpi=200)

if __name__ == "__main__":  

    # Check if arguments were actually passed
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        print("No arguments were provided.")

    config = load_config(config_path)

    #plot_histo_instrument(config['data']['path'])
    #plot_histo_dec(config['data']['path'])
    plot_histo_schedule(config)