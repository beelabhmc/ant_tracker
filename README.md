# Ant Tracker

These scripts can be used to count ant moving across a video. The pipeline works
by identifying "Regions of Interest", which are choke points through which the
ants must cross to travel from one area to another area, and then recording in
which ways the ants cross the regions during the video.

The code also supports painting red polyhedrons to denote the regions of interest
in the video, and the code can detect those regions automatically.

### Dependencies

The code in this repository runs on Python 3.7.0 and Matlab R2019A.

The python executables depend on the [numpy](https://www.numpy.org/),
[opencv](https://opencv.org/), [matplotlib](https://matplotlib.org/), and
[PIL](https://pillow.readthedocs.io/en/stable/) python packages, as well as
[ffmpeg](https://ffmpeg.org/). The code is also designed to be run as a
pipeline using [snakemake](https://snakemake.readthedocs.io/en/stable/).

The code does not yet automatically install its dependencies, so you have to
install all of those manually for it to work.

### Code Files

An explanation of all of the different code files in the project, WIP:

 - [ant_traking.m](scripts/ant_tracking.m) This file contains matlab code
   which takes footage of the ROIs and returns a dataframe containing all
   the ants which it saw and how they move. This script is called by track.py.
 - [combinetrack.py](scripts/combinetrack.py) This file takes tracks for
   each ROI and recombines each ROI down to one file (undoes split.py)
 - [constants.py](scripts/constants.py) This file contains various parameters
   which one may tweak to improve performance.
 - [croprotate.py](scripts/croprotate.py) Because track.py requires a video
   file which only contains the ROI, this file is necessary to crop and rotate
   the video to capture just the ROIs. It takes ROIs which are defined by
   roidetect.py.
 - [plot_tracks.py](scripts/plot_tracks.py) A python script which plots the
   tracks which matlab detects in an ROI. This is useful for observing the
   impact of tinkering with the parameters.
 - [roidetect.py](scripts/roidetect.py) A script which searches an image for
   red polygons painted in there, which it interprets as being ROIs and records
   them as such in a file.
 - [routes.py](scripts/routes.py) Code written for an old requirement (tracking
   which path ants take along ROIs), which is preserved in case that is ever
   useful in the future.
 - [split.py](scripts/split.py) Code which splits up videos into smaller chunks
   based on time (I recommend 10 minutes).
 - [track.py](scripts/track.py) Python code which interfaces with ant_tracking.m
   and saves the data that it outputs into a file in a nice format.
 - [tracktor.py](scripts/track.py) Legacy code from Arya which I don't yet know
   what it does.
 - [vid_meta_data.py](scripts/vid_meta_data.py) A script which reads the
   metadata from videos and contains functions with it common to multiple other
   python scripts.

