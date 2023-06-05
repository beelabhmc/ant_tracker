# absolute path pointing to video files
#
# NOTE: all dir paths should have trailing slashes
VID_DIR = '/Volumes/Storage/Ant_Tracking_Jarred/storage/'
# absolute path pointing to output dir
DIRECTORY = '/Volumes/Storage/Ant_Tracking_Jarred/out/'
# path pointing to split, crop, and result dirs
# must be relative to DIRECTORY
SPLIT_DIR ='split/'
CROP_DIR = 'crop/'
RESULT_VID_DIR = 'result/'

# These parameters are used only as default values. The actual values used are 
# stored in config.yaml.

# Parameters used by the python code that can be tweaked for better performance
PADDING = 10                    # This constant was buried in the antTracker.py
                                # file when I got it for the first time, but I
                                # can't find out where or if it is ever used by
                                # the code.

MIN_BLOB = 1                    # The smallest size of blob which is interpreted
                                # as an ant

COUNT_WARNING_THRESHOLD = 10    # If more ants than this are detected in the
                                # span of 5 seconds, throw a warning and flag
                                # the offending tracks


# Parameters used by the matlab code that can be tweaked for better performance
NUM_GAUSSIANS = 3               # The number of Gaussians to use in fitting
                                # the background

NUM_TRAINING_FRAMES = 120       # The number of frames from which to learn the
                                # background

MINIMUM_BACKGROUND_RATIO = 0.70 # The portion of training footage which should
                                # be considered to match the background

COST_OF_NONASSIGNMENT = 15.0    # The cost of not assigning a detection to a
                                # track or a track to a detection.
                                # Decreasing this makes it more likely to detect
                                # two ants as belonging to one track

INVISIBLE_FOR_TOO_LONG = 5      # If a newly-detected track does not appear in
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

MIN_DURATION = 1.5              # The minimum duration for which  
                                # a track must persist to be
                                # saved as an ant.

CANNY_THRESHOLD_ONE = 50        # The lower threshold value. Any 
                                # gradient magnitude below this 
                                # threshold will be considered as 
                                # not an edge

CANNY_THRESHOLD_TWO = 200       # The higher threshold value. Any 
                                # gradient magnitude above this 
                                # threshold will be considered as 
                                # an edge

CANNY_APERTURE_SIZE = 3         # Defines the Sobel kernel size 
                                # for gradient computation. 

THRESHOLDING_THRESHOLD = 88     # A grayscale value above 127  
                                # turns to 255 (white), below  
                                # turns to 0 (black)

                                # Note: tree branch greyscale
                                # value is around 200. The ant is
                                # around 78-85. The floor (behind
                                # branch) is around 90-110.

DILATING_MATRIX = 3             # The shape of structuring
                                # element. It is an elliptical
                                # shape in this case

TRACKER_DISTANCE_THRESHOLD = 10 # The distance threshold. When
                                # the threshold is exceeded, the
                                # track will be deleted and a new
                                # track will be created

TRACKER_TRACE_LENGTH = 10       # Trace path history length (good
                                # for debugging purposes)

NO_ANT_COUNTER_FRAMES_TOTAL = 100     # If the ant isn't detected for 
                                # 100 frames, we can safely assume
                                # it has left the track

EDGE_BORDER = 10                # Creates a border around the ROI.
                                # If the ant disappears within the
                                # border, we can assume it has 
                                # left an edge. Otherwise, the ant
                                # "disappeared" on the middle of 
                                # the track, which doesn't make 
                                # sense. The ant will be removed.


# Parameters used in detecting bridges automatically via looking for red
# For more information on the HSV color model, go to
# https://en.wikipedia.org/wiki/HSL_and_HSV
# NOT UTILIZED
HSV_HUE_TOLERANCE = 70  # How close the hue must be to red to be detected
                        # A measure of which color the pixel is

HSV_SAT_MINIMUM = 55    # The smallest saturation for the red to be detected
                        # A measure of how strongly colored the pixel is

HSV_VALUE_MINIMUM = 60  # The smallest value for the red to be detected
                        # A measure of how bright the pixel is

SMOOTH_OPEN_SIZE = 3    # The amount by which to open the mask (removes small
                        # details).

SMOOTH_DILATE_SIZE = 3  # The amount by which to expand the mask after opening

SMOOTH_CLOSE_SIZE = 13  # The amount by which to close the mask after dilating
                        # (fills in holes and combines adjacent figures).

POLYGON_EPSILON = 0.02  # The amount of deviation from the found shape which
                        # the program tolerates in the final result.
                        # If the output has too many sides, increase it. If the
                        # output has too few, descrease it.

ROI_BBOX_PADDING = 7    # The amount of padding to place around the detected
                        # polygon when converting a polygon to an ROI.

