from ffsplit import *
import math
from constants import *
import matlab.engine
import numpy as np
from vid_meta_data import *
import argparse


def trackOneClip(vidPath, cushion, W, H, minBlob, vidExport, result_path):
    eng = matlab.engine.start_matlab()
    # call the ant_tracking.m script and get the resulting dataframe
    # inputs:
    #   vidExport - boolean, whether we should export the result video
    #   minBlob - int, minimum blob area in pixels
    #   vidPath - string, absolute path to cropped vid
    #   result_path - string, path to the directory in which to store result videos
    df = eng.ant_tracking(vidExport, minBlob, vidPath, result_path)
    if df:
        track_result = np.array([["fName", "X", "Y"]])
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
            # get first position
            begin = antTrack[0,:]
            # get last position
            end = antTrack[-1,:]
            # get start and end coordinates
            # and width and height of the bounding boxes
            x0 = begin[0]
            y0 = begin[1]
            x1 = end[0]
            y1 = end[1]
            width0 = begin[2]
            height0 = begin[3]
            width1 = end[2]
            height1 = end[3]
            # attempt to determine X and Y directions
            directionX = "NA"
            directionY = "NA"
            if x0 <= cushion and x1+width1>=(W-cushion):
                directionX = "LR"
            elif (x0 + width0) >= (W-cushion) and x1 <= cushion:
                directionX = "RL"
            if  y0 <= cushion and (y1+height1)>= (H-cushion):
                directionY = "TB"
            elif  (y0+height0) >= (H-cushion) and y1<= cushion:
                directionY = "BT"
            # save results in np array so that we can return them soon
            track_result = np.append(track_result,  [[vidPath, directionX, directionY]], axis=0)
        # return the data without its header
        return track_result[1:,]
    return np.array([])

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
                            help='path to a directory in which to dump result videos')
    arg_parser.add_argument('--r',
                            dest = 'result',
                            required = True,
                            type=str,
                            help='path of array of results to output')
    arg_parser.add_argument('--c',
                            dest = 'cushion',
                            type=int,
                            default=10,
                            help='number of pixels as padding (default = 10)')
    arg_parser.add_argument('--m',
                            dest = 'minBlob',
                            type=int,
                            default=5,
                            help='minimum blob area in pixels (default = 5)')
    arg_parser.add_argument('--e',
                            dest = 'export',
                            type=bool,
                            default=False,
                            help='do we export result video (default = False)')
    args = arg_parser.parse_args()

    # track ants in each of the cropped videos
    result_array = np.array([["fName", "X", "Y"]])
    print "Tracking ants in " + args.cropVid
    # get height and width of video
    H, W = findVideoMetada(args.cropVid)
    # call matlab to track ants in a single cropped video
    track_result = trackOneClip(args.cropVid, args.cushion, W, H, args.minBlob, args.export, args.result_path)
    # keep track of the tracking results in a np array
    if track_result.size:
        result_array = np.concatenate((result_array, track_result), axis=0)
    # save the tracking results to disk
    np.savetxt(args.result, result_array, delimiter= ',', fmt='%s')

if __name__== "__main__":
    main()
