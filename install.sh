#!/bin/bash

git submodule update --recursive --init

pip install -e .

# Create directory structure
mkdir "./data_in"
mkdir "./data_out"
mkdir "./plots"