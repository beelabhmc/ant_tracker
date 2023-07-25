# Ant Tracker
These scripts can be used to count ants moving across a video. The pipeline works by identifying "Regions of Interest", which are choke points through which the ants must cross to travel from one area to another area, and then recording in which ways the ants cross the regions during the video.

If you're just interested in running the pipeline, look at [this first-time setup page](https://github.com/beelabhmc/ant_tracker/wiki/For-People-Looking-to-Run-the-Pipeline)

## Dependencies
The code in this repository runs on Python >= 3.9.0.

The python executables depend on the [numpy](https://www.numpy.org/),
[opencv](https://opencv.org/), and [matplotlib](https://matplotlib.org/)
python packages, as well as [ffmpeg](https://ffmpeg.org/). The code is also
designed to be run as a pipeline using
[snakemake](https://snakemake.readthedocs.io/en/stable/).

Important dependencies include: 
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


Dependency installation instructions are given in the [first-time setup page](https://github.com/beelabhmc/ant_tracker/wiki/For-People-Looking-to-Run-the-Pipeline). 

## Code Files

An explanation of all of the different code files in the project, WIP:

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
   each ROI and recombines each ROI down to one file. It also resolves ant 
   merger/unmerger conflicts and removes tracks that deemed unfit (for example,
   tracks that appear for too little of a time are deleted).
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
 - [detector.py](scripts/detector.py) Takes in a video frame and detects ants
   in that frame. Returns the coordinates of the ants detected as well as their
   areas. 
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
   them as such in a file. NOTE: you must indicate what year the videos were recorded
   in (currently either 2021 or 2023). There are differences in the ROIs which will
   result in an error if not properly indicated. If you are not satisfied with the 
   ROIs detected automatically, you can manually set the ROIs with 
   [roidefine.py](https://github.com/beelabhmc/ant_tracker/blob/master/scripts/roidefine.py).
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
   based on time (10 minutes recommended).
 - [track.py](scripts/track.py) A script that parses the config file and then
   calls track_one_clip.py.
 - [track_one_clip.py](scripts/track_one_clip.py) A script
   which takes footage of the ROIs and returns a dataframe containing all
   the ants which it saw and how they move. It records crucial information
   such as when ants were first/last detected.
 - [tracker.py](scripts/tracker.py) A script that assigns coordinates to 
   existing or new ant tracks. It also attempts to detect when and where
   mergers/unmergers occurred.