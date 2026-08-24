import pandas as pd
import numpy as np
import csv

# From https://stackoverflow.com/a/69796836
def get_delimiter(file_path, bytes = 4096):
    sniffer = csv.Sniffer()
    data = open(file_path, "r").read(bytes)
    delimiter = sniffer.sniff(data).delimiter
    return delimiter

def load_csv(fname):

    delimiter = get_delimiter(fname)
    df = pd.read_csv(fname, sep=delimiter)

    # Remove planets
    df = df[df.coordstype != 'PLANET']

    # Convert RA and DEC to degrees
    df['ra2000'] = np.rad2deg(df['ra2000'])
    df['dec2000'] = np.rad2deg(df['dec2000'])

    # Sort array by instrument and priority
    df = df.sort_values(by=['tagpriority', 'remaining'], ascending=[True, False])

    return df