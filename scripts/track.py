import numpy as np
import argparse
from track_one_clip import trackOneClip
import constants

COLUMN_NAMES = [['filename', 'id', 'x0', 'y0', 't0', 'x1', 'y1', 't1',
                 'number_warning', 'broken_track']]


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('source',
                            type=str,
                            help='The path to a video file in which we want to '
                                 'track the ants.')
    arg_parser.add_argument('result_path',
                            type=str,
                            help='The path to a directory in which to save the '
                                 'results of tracking ants.')
    arg_parser.add_argument('video_path',
                            type=str,
                            nargs='?',
                            default=None,
                            help='The path to a directory in which to dump'
                                 'result videos. If no path is given, then it '
                                 'does not export videos.')
    arg_parser.add_argument('raw_results',
                            type=str,
                            default='',
                            nargs='?',
                            help='Path of array of raw results to output. '
                                 'If no path is given, then it does not save '
                                 'the raw results.')
    # contour area
    arg_parser.add_argument('-m', '--min-blob',
                            dest='min_blob',
                            type=int,
                            default=constants.MIN_BLOB,
                            help='minimum blob area in pixels (default = '
                            '%d)' % constants.MIN_BLOB)
    # can just count number of centers
    arg_parser.add_argument('-c', '--count-threshold',
                            dest='count_threshold',
                            type=int,
                            default=constants.COUNT_WARNING_THRESHOLD,
                            help='A threshold which, if more than this many '
                                 'ants are seen in 5 seconds, causes the code '
                                 'to output a warning and flag the offending '
                                 'ants.')
    # guassian blur?
    arg_parser.add_argument('-g', '--num-gaussians',
                            dest='gaussians',
                            type=int,
                            default=constants.NUM_GAUSSIANS,
                            help='The number of gaussians to use when fitting '
                                 'the background.')
    # no
    # arg_parser.add_argument('-tf', '--training-frames',
    #                         dest='training_frames',
    #                         type=int,
    #                         default=constants.NUM_TRAINING_FRAMES,
    #                         help='The number of frames to use to fit the '
    #                              'backgrond.')
    # no
    # arg_parser.add_argument('-b', '--min-background',
    #                         dest='background',
    #                         type=float,
    #                         default=constants.MINIMUM_BACKGROUND_RATIO,
    #                         help='The minimum portion of frames which must '
    #                              'be included in the background.')
    # not sure what this is
    # arg_parser.add_argument('-n', '--nonassignment-cost',
    #                         dest='nonassignment_cost',
    #                         type=float,
    #                         default=constants.COST_OF_NONASSIGNMENT,
    #                         help='The cost of not assigning a detection to '
    #                              'an existing track.')
    # max_frames_to_skip  # could possibly rename
    arg_parser.add_argument('-it', '--invisible-threshold',
                            dest='invisible_threshold',
                            type=int,
                            default=constants.INVISIBLE_FOR_TOO_LONG,
                            help='The number of frames after which to forget '
                                 'a new, missing track.')
    # no (probably)
    # arg_parser.add_argument('-ot', '--old-age-threshold',
    #                         dest='old_age_threshold',
    #                         type=int,
    #                         default=constants.OLD_AGE_THRESHOLD,
    #                         help='The number of frames after which to make a '
    #                              'track immune to the invisible theshold.')
    # huh?
    # arg_parser.add_argument('-vt', '--visibility-threshold',
    #                         dest='visibility_threshold',
    #                         type=float,
    #                         default=constants.VISIBILITY_THRESHOLD,
    #                         help='The minimum fraction of frames which an ant '
    #                              'must appear in for its track to be counted.')
    # no
    # arg_parser.add_argument('-ki', '--kalman-initial',
    #                         dest='kalman_initial',
    #                         type=int,
    #                         nargs=2,
    #                         default=constants.KALMAN_INITIAL_ERROR,
    #                         help='The margin of error on the initial position '
    #                              'and velocity for the kalman filter.')
    # no
    # arg_parser.add_argument('-ko', '--kalman-motion',
    #                         dest='kalman_motion',
    #                         type=int,
    #                         nargs=2,
    #                         default=constants.KALMAN_MOTION_NOISE,
    #                         help='The amount of variation in position and '
    #                              'velocity expected by the kalman filter.')
    # no
    # arg_parser.add_argument('-km', '--kalman-measurement',
    #                         dest='kalman_measurement',
    #                         type=float,
    #                         default=constants.KALMAN_MEASUREMENT_NOISE,
    #                         help='The expected deviation of measurements from '
    #                              'the actual position.')
    # no (similar functionality to invisible for too long)
    # arg_parser.add_argument('-v', '--min-visible-count',
    #                         dest='min_visible',
    #                         type=int,
    #                         default=constants.MIN_VISIBLE_COUNT,
    #                         help='The number of frames which a track must have '
    #                              'already appeared in to be output.')
    # no  # maybe
    arg_parser.add_argument('-d', '--min-duration',
                            dest='min_duration',
                            type=float,
                            default=constants.MIN_DURATION,
                            help='The minimum duration (in seconds) for which '
                                 'a track must be present to be recorded '
                                 '(default 1.5 seconds).')
    # detector.py
    arg_parser.add_argument('-cto', '--canny-threshold-one',
                            dest='canny_threshold_one',
                            type=int,
                            default=constants.CANNY_THRESHOLD_ONE,
                            help='The lower threshold value. Any gradient magnitude '
                            'below this threshold will be considered as not an edge')
    arg_parser.add_argument('-ctt', '--canny-threshold-two',
                            dest='canny_threshold_two',
                            type=int,
                            default=constants.CANNY_THRESHOLD_TWO,
                            help='The higher threshold value. Any gradient magnitude '
                            'above this threshold will be considered as an edge')
    arg_parser.add_argument('-cas', '--canny-aperture-size',
                            dest='canny_aperture_size',
                            type=int,
                            default=constants.CANNY_APERTURE_SIZE,
                            help='Defines the Sobel kernel size for gradient computation.')
    arg_parser.add_argument('-tt', '--thresholding-threshold',
                            dest='thresholding_threshold',
                            type=int,
                            default=constants.THRESHOLDING_THRESHOLD,
                            help='A grayscale value above 127 turns to 255 (white), below '
                            'turns to 0 (black) Note: tree branch greyscale value is around' 
                            '200. The ant is around 78-85. The floor (behind branch) is '
                            'around 90-110.')
    arg_parser.add_argument('-dm', '--dilating-matrix',
                            dest='dilating_matrix',
                            type=int,
                            default=constants.DILATING_MATRIX,
                            help='The shape of structuring element. It is an elliptical '
                            'shape in this case')
    arg_parser.add_argument('-tdt', '--tracker-distance-threshold',
                            dest='tracker_distance_threshold',
                            type=int,
                            default=constants.TRACKER_DISTANCE_THRESHOLD,
                            help='The distance threshold. When the threshold is exceeded, '
                            'the track will be deleted and a new track will be created')
    arg_parser.add_argument('-ttl', '--tracker-trace-length',
                            dest='tracker_trace_length',
                            type=int,
                            default=constants.TRACKER_TRACE_LENGTH,
                            help='Trace path history length (good for debugging purposes)')
    arg_parser.add_argument('-nac', '--no-ant-counter-frames-total',
                            dest='no_ant_counter_frames_total',
                            type=int,
                            default=constants.NO_ANT_COUNTER_FRAMES_TOTAL,
                            help='If the ant is not detected for 100 frames, we can '
                            'safely assume it has left the track')
    arg_parser.add_argument('-eb', '--edge-border',
                            dest='edge_border',
                            type=int,
                            default=constants.EDGE_BORDER,
                            help="Creates a border around the ROI. If the ant "
                            "disappears within the border, we can assume it has left an "
                            "edge. Otherwise, the ant disappeared on the middle of the "
                            "track, which doesn't make sense. The ant will be removed.")
    arg_parser.add_argument('-db', '--debug',
                            dest='debug',
                            action='store_const',
                            const=True,
                            default=False,
                            help='Create a video player and display the tracking '
                            'mask. Useful for debugging.')
    args = arg_parser.parse_args()

    # track ants in each of the cropped videos
    _ = np.array(COLUMN_NAMES)
    print('Tracking ants in', args.source)
    # call matlab to track ants in a single cropped video
    export = args.video_path is not None
    print("videoPath is", args.video_path, "export is", export)
    if args.video_path == None:
        args.video_path = ''

    # print("The result path is", args.result_path)
    trackOneClip(args.source, export, args.result_path,
                 args.min_blob, args.count_threshold, args.gaussians,
                 args.invisible_threshold, args.min_duration,
                 args.canny_threshold_one, args.canny_threshold_two,
                 args.canny_aperture_size, args.thresholding_threshold, 
                 args.dilating_matrix, args.tracker_distance_threshold,
                 args.tracker_trace_length, args.no_ant_counter_frames_total,
                 args.edge_border, args.debug)

if __name__ == '__main__':
    main()

# source: C:\Users\brian\Desktop\Ant\kalman_filter_multi_object_tracking-master\rois\0 indiv\ROI_1.mp4
# result_path: C:\Users\brian\Desktop\Ant\kalman_filter_multi_object_tracking-master\my_attempt
# python .\transition.py "C:\Users\brian\Desktop\Ant\kalman_filter_multi_object_tracking-master\rois_from_default_video\ROI_20.mp4" "C:\Users\brian\Desktop\Ant\kalman_filter_multi_object_tracking-master\current_integration\" "C:\Users\brian\Desktop\Ant\kalman_filter_multi_object_tracking-master\current_integration\"