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
 - [ant_traking.m](scripts/ant_tracking.m) This file contains matlab code
   which takes footage of the ROIs and returns a dataframe containing all
   the ants which it saw and how they move. This script is called by track.py.
 - [combinetrack.py](scripts/combinetrack.py) This file takes tracks for
   each ROI and recombines each ROI down to one file (undoes split.py)
 - [constants.py](scripts/constants.py) This file contains various parameters
   which one may tweak to improve performance.
 - [crop.py](scripts/crop.py) An outdated code file which crops images along
   rectangular ROIs as defined by trainingImageLabeler.m, which I have ceased
   work on with the new ROI model made by roidetect.py and the need to support
   ROIs which may be rotated relative to the frame or may even be
   non-rectangular.
 - [croprotate.py](scripts/croprotate.py) Because track.py requires a video
   file which only contains the ROI, this file is necessary to crop and rotate
   the video to capture just the ROIs. It takes ROIs which are defined by
   roidetect.py.
 - [getBBox.py](scripts/getBBox) An outdated code file which reads bounding
   boxes for ROIs from a file. This functionality has been subsumed into
   croprotate.py and the ROI file format has been changed such that this file
   is no longer useful.
 - [getFirstFrame.py](scripts/getFirstFrame.py) An outdated code file which
   grabs the first frame from a video and saves it into a jpg file, for use
   with the older method of ROI detection.
 - [getFrame.bash](scripts/getFrame.bash) An outdated shell script which serves
   as a wrapper around ffmpeg for extracting a frame from a video at a given
   time. This was used for the older method of ROI detection.
 - [imageCrop.py](scripts/imageCrop.py) An outdated and poorly documented file
   that I inherited from Arya and don't know what it does, aside from that it
   isn't useful.
 - [plot_tracks.py](scripts/plot_tracks.py) A python script which plots the
   tracks which matlab detects in an ROI. This is useful for observing the
   impact of tinkering with the parameters.
 - [rename.py](scripts/rename.py) A script for automatically renaming video
   files. I inherited this from Arya and am not presently entirely sure of what
   it does.
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
 - [trainingImageLabeler.m](scripts/trainingImageLabeler.m) Code copied from the
   matlab source code for the older approach to ROIs, but which is no longer
   needed.
 - [vid_meta_data.py](scripts/vid_meta_data.py) A script which reads the
   metadata from videos and contains functions with it common to multiple other
   python scripts.

