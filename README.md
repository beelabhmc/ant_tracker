# Ant Tracker

These scripts can be used to count ants moving across a video. The pipeline works
by identifying "Regions of Interest", which are choke points through which the
ants must cross to travel from one area to another area, and then recording in
which ways the ants cross the regions during the video.

If you're just interested in running the pipeline, look at
[this page](https://github.com/beelabhmc/ant_tracker/wiki/For-People-Looking-to-Run-the-Pipeline)

### Dependencies

The code in this repository runs on Python >= 3.9.0 and Matlab R2019A.

The python executables depend on the [numpy](https://www.numpy.org/),
[opencv](https://opencv.org/), and [matplotlib](https://matplotlib.org/)
python packages, as well as [ffmpeg](https://ffmpeg.org/). The code is also
designed to be run as a pipeline using
[snakemake](https://snakemake.readthedocs.io/en/stable/).

The code does not yet automatically install its dependencies, so you have to
install all of those manually for it to work.

Make sure to add these dependencies: 
- numpy
- cv2
- os
- math
- argparse
- re
- subprocess
- concurrent.futures
- matplotlib
- networkx
- Skimage (scikit-image)
- sklearn
- numba
- ffmpeg


If you are using a miniconda environment to run the pipeline, you can use the following command on requirements.txt to get all the necessary packages into an environment. `conda install --file requirements.txt`


### Code Files

An explanation of all of the different code files in the project, WIP:

 - [ant_traking.m](scripts/ant_tracking.m) This file contains matlab code
   which takes footage of the ROIs and returns a dataframe containing all
   the ants which it saw and how they move. This script is called by track.py.
 - [bbox.py](scripts/bbox.py) This file contains some functions which deal with
   regions of interest and bounding boxes and are used by several different
   scripts in the pipeline.
 - [check-dependencies.py](scripts/checkdependencies.py) This is a file which
   attempts to check for all of the dependencies that the script needs, and
   lists everything which needs to be installed to run.
 - [combinerois.py](scripts/combinerois.py) This file takes the separate files
   for each ROI and combines them into one file which contains, for each ant
   which was observed crossing the ROI, the ROI it crossed, it's initial and
   final edge crossings, and the corresponding timestamps.
 - [combinetrack.py](scripts/combinetrack.py) This file takes tracks for
   each ROI and recombines each ROI down to one file (undoes split.py)
 - [constants.py](scripts/constants.py) This file contains various parameters
   which one may tweak to improve performance. I am in the process of removing
   this file and moving all the constants into [config.yaml](config.yaml).
 - [convexify.py](scripts/convexify.py) This file contains a function to turn an
   arbitrary simple polygon into its
   [convex hull](https://en.wikipedia.org/wiki/Convex_hull). I had to write it
   because the default function in OpenCV does not work for all polygons.
 - [croprotate.py](scripts/croprotate.py) Because track.py requires a video
   file which only contains the ROI, this file is necessary to crop and rotate
   the video to capture just the ROIs. It takes ROIs which are defined by
   roidetect.py.
 - [edgefromtrack.py](scripts/edgefromtrack.py) A script which converts the
   output of track.py from containing x,y coordinates to containing which side
   the ant entered on and which side the ant exited on.
 - [metadata.py](scripts/vid_meta_data.py) A script which reads the
   metadata from videos and contains functions with it common to multiple other
   python scripts.
 - [pipeline.py](pipeline.py) A script made to allow easier execution of the
   pipeline by figuring out which arguments to pass to snakemake.
 - [plot_tracks.py](scripts/plot_tracks.py) A python script which plots the
   tracks which matlab detects in an ROI. This is useful for observing the
   impact of tinkering with the parameters.
 - [roidefine.py](scripts/roidefine.py) A script which allows you to manually
   specify the ROIs in a file, as an alternative to automatic ROI detection
   if your nest doesn't have the rois marked in red.
 - [roidetect.py](scripts/roidetect.py) A script which searches an image for
   red polygons painted in there, which it interprets as being ROIs and records
   them as such in a file.
 - [roilabel.py](scripts/roilabel.py) A script which takes the first frame of a
   video and draws the regions on interest onto it, then saves it to a file.
   This is also for exporting to human-readable and not necessary for the code
   to run.
 - [roimodify.py](scripts/roimodify.py) A script which allows people to take an
   existing ROI file and modify it.
 - [roipoly.py](scripts/roipoly.py) A script which contains a modified version
   of the [roipoly.py](https://github.com/jdoepfert/roipoly.py) repo.
   This is used for the manual labeling of regions of interest.
 - [split.py](scripts/split.py) Code which splits up videos into smaller chunks
   based on time (I recommend 10 minutes).
 - [track.py](scripts/track.py) Python code which interfaces with ant_tracking.py
   and saves the data that it outputs into a file in a csv file.

