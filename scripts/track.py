import math
import matlab.engine
import numpy as np
import argparse
from os.path import abspath

import metadata
import constants


def trackOneClip(vidPath, W, H, vidExport, result_path,
        minBlob=constants.MIN_BLOB,
        num_gaussians=constants.NUM_GAUSSIANS,
        num_training_frames=constants.NUM_TRAINING_FRAMES,
        minimum_background_ratio=constants.MINIMUM_BACKGROUND_RATIO,
        cost_of_nonassignment=constants.COST_OF_NONASSIGNMENT,
        invisible_for_too_long=constants.INVISIBLE_FOR_TOO_LONG,
        old_age_threshold=constants.OLD_AGE_THRESHOLD,
        visibility_threshold=constants.VISIBILITY_THRESHOLD,
        kalman_initial_error=constants.KALMAN_INITIAL_ERROR,
        kalman_motion_noise=constants.KALMAN_MOTION_NOISE,
        kalman_measurement_noise=constants.KALMAN_MEASUREMENT_NOISE,
        min_visible_count=constants.MIN_VISIBLE_COUNT):
    eng = matlab.engine.start_matlab()
    # call the ant_tracking.m script and get the resulting dataframe
    # inputs:
    #   vidPath - string, absolute path to cropped vid
    #   vidExport - boolean, whether we should export the result video
    #   result_path - string, path to the directory in which to store
    #                 result videos
    #   minBlob - int, minimum blob area in pixels
    eng.addpath('scripts')
    df = eng.ant_tracking(abspath(vidPath), vidExport, abspath(result_path),
                          minBlob, num_gaussians, num_training_frames,
                          minimum_background_ratio, cost_of_nonassignment,
                          invisible_for_too_long, old_age_threshold,
                          visibility_threshold,
                          matlab.double(kalman_initial_error),
                          matlab.double(kalman_motion_noise),
                          kalman_measurement_noise, min_visible_count)
    if df:
        track_result = np.array([['filename', 'id', 'x0', 'y0', 't0',
                                  'x1', 'y1', 't1']])
        print(df[:10])
        # convert the dataframe to a np array
        # it should have five columns:
        #   x_pos, y_pos, width, height, ant_id
        df = np.array(df)
        # get ant IDs as the unique values of the last column of the df
        idL = set(df[:, 4])
        # for each ant that appears in the video...
        for idnum in idL:
            # get tracks for this ant
            antTrack = df[df[:, 4] == idnum]
            # NOTE: x and y coords can be negative if kalman filter is
            #       predicting the ant after it passes out of frame
            x0 = antTrack[0,0]
            x1 = antTrack[-1,0]
            y0 = antTrack[0,1]
            y1 = antTrack[-1,1]
            t0 = antTrack[0,5]
            t1 = antTrack[-1,5]
            if (x1-x0)**2 + (y1-y0)**2 < 100:
                # Skip "ants" who don't move, as these tracks are likely fake
                continue
            # save results in np array so that we can return them soon
            track_result = np.append(track_result, [[vidPath, idnum, x0, y0, t0,
                                                     x1, y1, t1]],
                                     axis=0)
        # return the data without its header
        return track_result[1:,], df
    return np.array([]), np.array([])

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--m',
                            dest = 'minBlob',
                            type=int,
                            default=constants.MIN_BLOB,
                            help='minimum blob area in pixels (default = '
                            '%d)' % constants.MIN_BLOB)
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

    args = arg_parser.parse_args()

    # track ants in each of the cropped videos
    result_array = np.array([['fName', 'id', 'x0', 'y0', 't0',
                              'x1', 'y1', 't1']])
    print('Tracking ants in', args.source)
    # get height and width of video
    H, W = metadata.get_video_dimensions(args.source)
    # call matlab to track ants in a single cropped video
    export = args.video_path is not None
    track_result, raw_results = trackOneClip(args.source, W, H, export,
                                             args.video_path or '')
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

