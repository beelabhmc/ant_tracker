import numpy as np
import argparse
from track_one_clip import *
import constants


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('source',
                            type=str,
                            help='The path to a video file in which we want to '
                                 'track the ants.')
    arg_parser.add_argument('history_path',
                            type=str,
                            help='The path to a directory in which to save the '
                                 'history csv.')
    arg_parser.add_argument('video_path',
                            type=str,
                            nargs='?',
                            default=None,
                            help='The path to a directory in which to dump'
                                 'annotated result videos. If no path is given, then it '
                                 'does not export videos.')
    arg_parser.add_argument('-m', '--min-blob',
                            dest='min_blob',
                            type=int,
                            default=constants.MIN_BLOB,
                            help='minimum blob area in pixels (default = '
                            '%d)' % constants.MIN_BLOB)
    arg_parser.add_argument('-c', '--count-threshold',
                            dest='count_threshold',
                            type=int,
                            default=constants.COUNT_WARNING_THRESHOLD,
                            help='A threshold which, if more than this many '
                                 'ants are seen in 5 seconds, causes the code '
                                 'to output a warning and flag the offending '
                                 'ants.')
    arg_parser.add_argument('-g', '--num-gaussians',
                            dest='gaussians',
                            type=int,
                            default=constants.NUM_GAUSSIANS,
                            help='Guassian blur')
    arg_parser.add_argument('-it', '--invisible-threshold',
                            dest='invisible_threshold',
                            type=int,
                            default=constants.INVISIBLE_FOR_TOO_LONG,
                            help='The number of frames after which to forget '
                                 'a new, missing track.')
    arg_parser.add_argument('-d', '--min-duration',
                            dest='min_duration',
                            type=float,
                            default=constants.MIN_DURATION,
                            help='The minimum duration (in seconds) for which '
                                 'a track must be present to be recorded ')
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
    arg_parser.add_argument('-md', '--merge-distance',
                            dest='merge_distance',
                            type=int,
                            default=constants.MERGE_DISTANCE,
                            help="The maximum distance allowed between two existing tracks"
                            "for it to be considered a merger.")
    arg_parser.add_argument('-au', '--auto',
                            dest='automatic',
                            action='store_const',
                            const=True,
                            default=False,
                            help='Determines whether or not unmerging will be done automatically. '
                            'Warning: Prone to falsities for multiple ants')
    arg_parser.add_argument('-db', '--debug',
                            dest='debug',
                            action='store_const',
                            const=True,
                            default=False,
                            help='Create a video player and display the tracking '
                            'mask. Useful for debugging.')
    args = arg_parser.parse_args()

    print('Tracking ants in', args.source)
    # call matlab to track ants in a single cropped video
    export = args.video_path is not None

    if args.video_path == None:
        args.video_path = ''

    print(args.history_path)
    tracker_object = trackOneClip(args.source, args.video_path, export,
                 args.min_blob, args.gaussians,
                 args.canny_threshold_one, args.canny_threshold_two,
                 args.canny_aperture_size, args.thresholding_threshold, 
                 args.dilating_matrix, args.tracker_distance_threshold,
                 args.tracker_trace_length, args.no_ant_counter_frames_total,
                 args.edge_border, args.merge_distance)

    # makes the history csvs
    final_result_path_history = make_history_CSV(tracker_object, args.history_path)

    # this makes the intermediate directories "merger" and "merger_annotated"
    roi = os.path.splitext(os.path.basename(args.history_path))[0]
    split = os.path.dirname(args.history_path)
    video = os.path.dirname(split)
    intermediate = os.path.dirname(os.path.dirname(video))

    split = split.split('/')[-1]
    video = video.split('/')[-1]

    merger_dir = os.path.join(os.path.join(os.path.join(os.path.join(intermediate, "merger"), video), split), roi)
    merger_annotated_dir = os.path.join(os.path.join(os.path.join(os.path.join(intermediate, "merger_annotated"), video), split), roi)

    # makes the merge videos
    make_merge_vids(final_result_path_history, args.source, args.video_path, merger_dir, merger_annotated_dir)


if __name__ == '__main__':
    main()