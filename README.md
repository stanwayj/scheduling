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
If this package is installed via conda you will have to enter the conda enviroment each time you would like to use the package. To enter the enviroment use the command:
```bash
$ conda activate schedule
```
To leave the enviroment afterwards, use the command:
```bash
$ conda deactivate
```
To remove the conda enviroment, use the command:
```bash
$ conda remove -n schedule --all
```