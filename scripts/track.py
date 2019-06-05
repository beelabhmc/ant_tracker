import math
import matlab.engine
import numpy as np
import argparse

import vid_meta_data as metadata
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
    df = eng.ant_tracking(vidPath, vidExport, result_path, minBlob, 
                          num_gaussians, num_training_frames,
                          minimum_background_ratio, cost_of_nonassignment,
                          invisible_for_too_long, old_age_threshold,
                          visibility_threshold, kalman_initial_error,
                          kalman_motion_noise, kalman_measurement_noise,
                          min_visible_count)
    if df:
        track_result = np.array([["fName", "id", "X", "Y"]])
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
            x0 = antTrack[-1,0]
            x1 = antTrack[0,0]
            directionX = x0-x1
            y0 = antTrack[-1,1]
            y1 = antTrack[0,1]
            directionY = y0-y1
            # save results in np array so that we can return them soon
            track_result = np.append(track_result, [[vidPath, idnum, directionX,
                                                     directionY]],
                                     axis=0)
        # return the data without its header
        return track_result[1:,], df
    return np.array([]), np.array([])

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--i',
                            dest = 'cropVid',
                            required = True,
                            type=str,
                            help='path to a video to track')
    arg_parser.add_argument('--o',
                            dest = 'result_path',
                            required = True,
                            type=str,
                            help='path to a directory in which to dump'
                                 'result videos')
    arg_parser.add_argument('--r',
                            dest = 'result',
                            required = True,
                            type=str,
                            help='path of array of results to output')
    arg_parser.add_argument('--rr',
                            dest = 'raw_results',
                            type=str,
                            default=None,
                            help='path of array of raw results to output'
                                 '(default = None)')
    arg_parser.add_argument('--m',
                            dest = 'minBlob',
                            type=int,
                            default=constants.DEFAULT_MIN_BLOB,
                            help='minimum blob area in pixels (default = '
                            '%d)' % constants.DEFAULT_MIN_BLOB)
    arg_parser.add_argument('--e',
                            dest = 'export',
                            type=bool,
                            default=False,
                            help='do we export result video (default = False)')

    args = arg_parser.parse_args()

    # track ants in each of the cropped videos
    result_array = np.array([["fName", "id", "X", "Y"]])
    print("Tracking ants in " + args.cropVid)
    # get height and width of video
    H, W = metdata.get_video_dimensions(args.cropVid)
    # call matlab to track ants in a single cropped video
    track_result, raw_results = trackOneClip(args.cropVid, W, H, args.minBlob,
                                             args.export, args.result_path)
    # keep track of the tracking results in a np array
    if track_result.size:
        result_array = np.concatenate((result_array, track_result), axis=0)
    # save the tracking results to disk
    np.savetxt(args.result, result_array, delimiter= ',', fmt='%s')
    # save the raw results to disk
    if args.raw_results is not None:
        np.savetxt(args.raw_results, raw_results, delimiter=',', fmt='%s')

if __name__== "__main__":
    main()

