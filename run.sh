#!/bin/bash

# Load arguments from command line argument
option1=$1

# Option must either be clean, or a configuration file
# If option1 is clean, clean data and plots, then kill operation
if [[ "$option1" == "clean" ]]; then
    echo "Cleaning data and plot directories"
    rm "./plots"/*
    rm "./data_in"/*
    rm "./data_out"/*
    exit 1
elif [[ "$option1" == *.yaml ]]; then
    echo "Plotting summary and running schedule from $option1"
    python3 ./src/schedule.py "$option1"
    python3 ./src/plot_summary.py "$option1"    
else
    echo "The first command line argument must be ``clean'' or a yaml configuration file"
fi
