# absolute path pointing to video files
#
# NOTE: all dir paths should have trailing slashes
VID_DIR = "/Volumes/Storage/Ant_Tracking_Jarred/storage/"
# absolute path pointing to output dir
DIRECTORY = "/Volumes/Storage/Ant_Tracking_Jarred/out/"
# path pointing to split, crop, and result dirs
# must be relative to DIRECTORY
SPLIT_DIR ="split/"
CROP_DIR = "crop/"
RESULT_VID_DIR = "result/"


# Parameters used by the python code that can be tweaked for better performance
PADDING = 10 # This constant was buried in the antTracker.py file when I got
             # it for the first time, but I can't find out where or if it is
             # ever used by the code.

MIN_BLOB = 5 # The smallest size of blob which is interpreted as an ant


# Parameters used by the matlab code that can be tweaked for better performance
NUM_GAUSSIANS = 5               # The number of Gaussians to use in fitting
                                # the background

NUM_TRAINING_FRAMES = 40        # The number of frames from which to learn the
                                # background

MINIMUM_BACKGROUND_RATIO = 0.70 # The portion of training footage which should
                                # be considered to match the background

COST_OF_NONASSIGNMENT = 15.0    # The cost of not assigning a detection to a
                                # track or a track to a detection.
                                # Decreasing this makes it more likely to detect
                                # two ants as belonging to one track

INVISIBLE_FOR_TOO_LONG = 4      # If a newly-detected track does not appear in
                                # this many frames, assume it was not a real ant

OLD_AGE_THRESHOLD = 8           # If a track exists for this many frames, then
                                # it is immune to being removed for being
                                # invisible for too long

VISIBILITY_THRESHOLD = 0.6      # If an ant is visible in less than this
                                # proportion of frames, then assume that isn't
                                # real

KALMAN_INITIAL_ERROR = [200, 50]# The margin of error in the initial position
                                # and velocity for the Kalman filter

KALMAN_MOTION_NOISE = [100, 15] # The exactitude with which the Kalman filter
                                # insists on its expectations

KALMAN_MEASUREMENT_NOISE = 100. # The expected margin of error in the
                                # observations from the footage.

MIN_VISIBLE_COUNT = 3           # The minimum number of frames for which an ant
                                # must be spotted for its track to be displayed

