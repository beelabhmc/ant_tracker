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
pipeline using snakemake

The code does not yet automatically install its dependencies, so you have to
install all of those manually for it to work.

### Code Files

An explanation of all of the different code files in the project, WIP:

 - [antTracker.py](scripts/antTracker.py) An outdate code file which would
   process videos from beginning to end in one sweep. This file is no longer
   being maintained because the pipeline approach is much more flexible and
   more easily maintainable.
 - [ant_traking.m](scripts/ant_tracking.m

