#!/bin/bash

# TODO: 
# 1. make the argument accept parameter file
# 2. explain different arguments


# Load argument from command line argument
argument=$1

# If argument is clean, clean data and plots, then kill operation
if [[ "$argument" == "clean" ]]; then
    echo "Cleaning data and plot directories"
    rm "./plots"/*
    rm "./data_in"/*
    rm "./data_out"/*
    exit 1
fi

# Make directory for plots
PLOTS_DIR="plots"

if [ ! -d "$PLOTS_DIR" ]; then
    mkdir "$PLOTS_DIR"
    echo "Made plots directory"
else
    echo "Plot directory exists. Skipping"
fi

# Plot basic summary of observations
python3 ./src/plot_summary.py "$argument"

# Run schedule
python3 ./src/schedule.py "$argument"