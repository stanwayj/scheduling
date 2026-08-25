import matplotlib.pyplot as plt
import numpy as np
import sys

from src import *

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


if __name__ == "__main__":  

    # Check if arguments were actually passed
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        print("No arguments were provided.")

    config = load_config(config_path)

    plot_histo_instrument(config['data']['path'])
    plot_histo_dec(config['data']['path'])