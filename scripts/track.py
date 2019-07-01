import math
import matlab.engine
import numpy as np
import argparse
from os.path import abspath
import collections

import metadata
import constants

COLUMN_NAMES = [['filename', 'id', 'x0', 'y0', 't0', 'x1', 'y1', 't1',
                 'number_warning']]

def trackOneClip(vidPath, vidExport, result_path,
        minBlob=constants.MIN_BLOB,
        count_warning_threshold=constants.COUNT_WARNING_THRESHOLD,
        num_gaussians=constants.NUM_GAUSSIANS,
        num_training_frames=constants.NUM_TRAINING_FRAMES,
        minimum_background_ratio=constants.MINIMUM_BACKGROUND_RATIO,
        cost_of_nonassignment=constants.COST_OF_NONASSIGNMENT,
        invisible_threshold=constants.INVISIBLE_FOR_TOO_LONG,
        old_age_threshold=constants.OLD_AGE_THRESHOLD,
        visibility_threshold=constants.VISIBILITY_THRESHOLD,
        kalman_initial_error=constants.KALMAN_INITIAL_ERROR,
        kalman_motion_noise=constants.KALMAN_MOTION_NOISE,
        kalman_measurement_noise=constants.KALMAN_MEASUREMENT_NOISE,
        min_visible_count=constants.MIN_VISIBLE_COUNT):
    # call the ant_tracking.m script and get the resulting dataframe
    # inputs:
    #   vidPath - string, absolute path to cropped vid
    #   vidExport - boolean, whether we should export the result video
    #   result_path - string, path to the directory in which to store
    #                 result videos
    #   minBlob - int, minimum blob area in pixels
    #   other inputs are documented in scripts/constants.py
    eng = matlab.engine.start_matlab()
    eng.addpath('scripts')
    df = eng.ant_tracking(abspath(vidPath), vidExport, abspath(result_path),
                          minBlob, num_gaussians, num_training_frames,
                          minimum_background_ratio, cost_of_nonassignment,
                          invisible_threshold, old_age_threshold,
                          visibility_threshold,
                          matlab.double(kalman_initial_error),
                          matlab.double(kalman_motion_noise),
                          kalman_measurement_noise, min_visible_count)
    if df:
        track_result = np.array(COLUMN_NAMES)
        fps = metadata.get_video_fps(vidPath)
        # Get the framerate of the video
        # convert the dataframe to a np array
        # it should have five columns:
        #   x_pos, y_pos, width, height, ant_id, framenumbet
        df = np.array(df)
        # get ant IDs as the unique values of the last column of the df
        id_list = set(df[:, 4])
        # for each ant that appears in the video...
        for idnum in id_list:
            # get tracks for this ant
            antTrack = df[df[:, 4] == idnum]
            antTrack = antTrack[antTrack[:, -1] == 1]
            antTrack = antTrack[:,:-1]
            # NOTE: x and y coords can be negative if kalman filter is
            #       predicting the ant after it passes out of frame
            x0 = antTrack[0,0]
            x1 = antTrack[-1,0]
            y0 = antTrack[0,1]
            y1 = antTrack[-1,1]
            t0 = round(antTrack[0,5]/fps, 2)
            t1 = round(antTrack[-1,5]/fps, 2)
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
            # save results in np array so that we can return them soon
            track_result = np.append(track_result, [[vidPath, idnum, x0, y0, t0,
                                                     x1, y1, t1, 0]],
                                     axis=0)
        # Iterate through the resulting dataframe and flag unexpected quantities
        times = collections.deque()
        for i in range(1, len(track_result)):
            vid, idnum, x0, y0, t0, x1, y1, t1, flag = track_result[i]
            times.append((float(t1), i))
            while times[0][0] <= float(t1)-5:
                times.popleft()
            if len(times) >= count_warning_threshold:
                print('Warning: detected an unexpected number of tracks at '
                      f't={t1} in {vidPath}')
                for t, index in times:
                    track_result[index, 8] = 1
        # return the data without its header
        return track_result[1:,], df
    return np.array([]), np.array([])

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
    args = arg_parser.parse_args()

    # track ants in each of the cropped videos
    result_array = np.array(COLUMN_NAMES)
    print('Tracking ants in', args.source)
    # call matlab to track ants in a single cropped video
    export = args.video_path is not None
    track_result, raw_results \
        = trackOneClip(args.source, export, args.video_path or '',
                        args.min_blob, args.count_threshold, args.gaussians,
                        args.training_frames, args.background,
                        args.nonassignment_cost, args.invisible_threshold,
                        args.old_age_threshold, args.visibility_threshold,
                        args.kalman_initial, args.kalman_motion,
                        args.kalman_measurement, args.min_visible)
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

