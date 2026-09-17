# Scheduler
Software to schedule long-term telescope observations. Developed for the JCMT, but should be easily applied to any observatory.

## Installing
There are two methods to install this package, pip and conda.

To install via pip use the following commands:
```bash
$ git clone https://github.com/stanwayj/scheduling.git
$ cd scheduling/
$ pip3 install -e .
```

To install via conda use the following commands:
```bash
$ conda env create -f environment.yaml
$ conda activate schedule
$ pip3 install -e .
```
If this package is installed via conda you will have to enter the conda enviroment each time you would like to use the package.
