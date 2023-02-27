import ant_tracking
import numpy as np
import argparse
from os.path import abspath
import collections
import metadata
import constants
import cv2
import copy

COLUMN_NAMES = [['filename', 'id', 'x0', 'y0', 't0', 'x1', 'y1', 't1',
                 'number_warning', 'broken_track']]


# def trackOneClip(
#         vidPath, vidExport, result_path, minBlob, count_warning_threshold,
#         num_gaussians, num_training_frames, minimum_background_ratio,
#         cost_of_nonassignment, invisible_threshold, old_age_threshold,
#         visibility_threshold, kalman_initial_error, kalman_motion_noise,
#         kalman_measurement_noise, min_visible_count, min_duration, debug):


def track(vidPath):
    cap = cv2.VideoCapture(vidPath)
                
    detector = ant_tracking.Detectors()
    """Initialize variable used by Tracker class
    Args:
        dist_thresh: distance threshold. When exceeds the threshold,
                        track will be deleted and new track is created
        max_frames_to_skip: maximum allowed frames to be skipped for
                            the track object undetected
        max_trace_lenght: trace path history length
        trackIdCount: identification of each track object
    Return:
        None
    """
    tracker = ant_tracking.Tracker(50, 1000000, 10, 1)

    results = []

    frame_idx = 1
    while(True):
        ret, frame = cap.read()
        
        if ret == True:

            orig_frame = copy.copy(frame)
            centers = detector.Detect(frame)
            if (len(centers) > 0):
                
                tracker.Update(centers)

                for i in range(len(tracker.tracks)):
                    if (len(tracker.tracks[i].trace) > 1):
                        for j in range(len(tracker.tracks[i].trace)-1):
                            x1 = tracker.tracks[i].trace[j][0][0]
                            y1 = tracker.tracks[i].trace[j][1][0]
                            x2 = tracker.tracks[i].trace[j+1][0][0]
                            y2 = tracker.tracks[i].trace[j+1][1][0]
                            ant_id = tracker.tracks[i].track_id
                            
                            res = (x1, y1, ant_id, frame_idx)
                            results.append(res)
                
            frame_idx += 1
                            
        else:
            cap.release()
            return results


def formatResults(results, vidPath, min_duration):
    track_result = np.array(COLUMN_NAMES)

    cap = cv2.VideoCapture(vidPath)  # TO DO: prob just get this from the original function
    fps = cap.get(cv2.CAP_PROP_FPS)

    x = results[:,0]
    y = results[:,1]

    df = np.array(results)
    id_list = set(df[:, 2])

    for idnum in id_list:
        antTrack = df[df[:, 2] == idnum]  # get tracks for that ant
        x0 = antTrack[0,0]
        x1 = antTrack[-1,0] 
        y0 = antTrack[0,1]
        y1 = antTrack[-1,1] 
        
        t0 = round(antTrack[0,3]/fps, 2)
        t1 = round(antTrack[-1,3]/fps, 2)
        
        if (x1-x0)**2 + (y1-y0)**2 < 100:
            # These ants appeared and disappeared close together
            for x, y, *_ in antTrack:
                if (x-x0)**2 + (y-y0)**2 > 100:
                    # The ant moved a bit and then turned around and
                    # went back
                    # This track still counts
                    break
            else:
                # This blob never traveled far, so it is likely fake
                continue
        
        if t1-t0 < min_duration:
            continue

    # save results in np array so that we can return them soon
    track_result = np.append(track_result, [[vidPath, idnum, x0, y0, t0,
                                             x1, y1, t1, 0, 0]], axis=0)

    # return data w/o its header
    return track_result[1:,], df


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
    arg_parser.add_argument('-m', '--min-blob',
                            dest = 'min_blob',
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
                            help='The number of gaussians to use when fitting '
                                 'the background.')
    arg_parser.add_argument('-tf', '--training-frames',
                            dest='training_frames',
                            type=int,
                            default=constants.NUM_TRAINING_FRAMES,
                            help='The number of frames to use to fit the '
                                 'backgrond.')
    arg_parser.add_argument('-b', '--min-background',
                            dest='background',
                            type=float,
                            default=constants.MINIMUM_BACKGROUND_RATIO,
                            help='The minimum portion of frames which must '
                                 'be included in the background.')
    arg_parser.add_argument('-n', '--nonassignment-cost',
                            dest='nonassignment_cost',
                            type=float,
                            default=constants.COST_OF_NONASSIGNMENT,
                            help='The cost of not assigning a detection to '
                                 'an existing track.')
    arg_parser.add_argument('-it', '--invisible-threshold',
                            dest='invisible_threshold',
                            type=int,
                            default=constants.INVISIBLE_FOR_TOO_LONG,
                            help='The number of frames after which to forget '
                                 'a new, missing track.')
    arg_parser.add_argument('-ot', '--old-age-threshold',
                            dest='old_age_threshold',
                            type=int,
                            default=constants.OLD_AGE_THRESHOLD,
                            help='The number of frames after which to make a '
                                 'track immune to the invisible theshold.')
    arg_parser.add_argument('-vt', '--visibility-threshold',
                            dest='visibility_threshold',
                            type=float,
                            default=constants.VISIBILITY_THRESHOLD,
                            help='The minimum fraction of frames which an ant '
                                 'must appear in for its track to be counted.')
    arg_parser.add_argument('-ki', '--kalman-initial',
                            dest='kalman_initial',
                            type=int,
                            nargs=2,
                            default=constants.KALMAN_INITIAL_ERROR,
                            help='The margin of error on the initial position '
                                 'and velocity for the kalman filter.')
    arg_parser.add_argument('-ko', '--kalman-motion',
                            dest='kalman_motion',
                            type=int,
                            nargs=2,
                            default=constants.KALMAN_MOTION_NOISE,
                            help='The amount of variation in position and '
                                 'velocity expected by the kalman filter.')
    arg_parser.add_argument('-km', '--kalman-measurement',
                            dest='kalman_measurement',
                            type=float,
                            default=constants.KALMAN_MEASUREMENT_NOISE,
                            help='The expected deviation of measurements from '
                                 'the actual position.')
    arg_parser.add_argument('-v', '--min-visible-count',
                            dest='min_visible',
                            type=int,
                            default=constants.MIN_VISIBLE_COUNT,
                            help='The number of frames which a track must have '
                                 'already appeared in to be output.')
    arg_parser.add_argument('-d', '--min-duration',
                            dest='min_duration',
                            type=float,
                            default=1.5,
                            help='The minimum duration (in seconds) for which '
                                 'a track must be present to be recorded '
                                 '(default 1.5 seconds).')
    arg_parser.add_argument('-db', '--debug',
                            dest='debug',
                            action='store_const',
                            const=True,
                            default=False,
                            help='Create a video player and display the tracking '
                                'mask. Useful for debugging.')
    args = arg_parser.parse_args()

    # track ants in each of the cropped videos
    result_array = np.array(COLUMN_NAMES)
    print('Tracking ants in', args.source)
    
    print(args.source)
    results = np.array(track(args.source))
    track_result, raw_results = formatResults(results, args.source, args.min_duration)

    # track_result, raw_results \
    #     = trackOneClip(args.source, export, args.video_path or '',
    #                     args.min_blob, args.count_threshold, args.gaussians,
    #                     args.training_frames, args.background,
    #                     args.nonassignment_cost, args.invisible_threshold,
    #                     args.old_age_threshold, args.visibility_threshold,
    #                     args.kalman_initial, args.kalman_motion,
    #                     args.kalman_measurement, args.min_visible,
    #                     args.min_duration, args.debug)

    # keep track of the tracking results in a np array
    if track_result.size:
        result_array = np.concatenate((result_array, track_result), axis=0)
    # save the tracking results to disk
    np.savetxt(args.result_path, result_array, delimiter= ',', fmt='%s')
    # save the raw results to disk
    if args.raw_results:
        np.savetxt(args.raw_results, raw_results, delimiter=',', fmt='%s')

if __name__== '__main__':
    main()

