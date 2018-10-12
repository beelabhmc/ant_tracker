from ffsplit import *
import math
from constants import *
import matlab.engine
import numpy as np


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
        df = np.array(df)
        idL = set(df[:, 4])
        for idnum in idL:
            antTrack = df[df[:, 4] == idnum]
            begin = antTrack[1,:]
            end = antTrack[-1,:]
            x0 = begin[0]
            y0 = begin[1]
            x1 = end[0]
            y1 = end[1]
            width0 = begin[2]
            height0 = begin[3]
            width1 = end[2]
            height1 = end[3]
            directionX = "NA"
            directionY = "NA"
            if x0  <= cushion and x1+width1>=(W-cushion):
                directionX = "LR"
            elif (x0 + width0) >= (W-cushion) and x1 <= cushion:
                directionX = "RL"
            if  y0 <= cushion and (y1+height1)>= (H-cushion):
                directionY = "TB"
            elif  (y0+height0) >= (H-cushion) and y1<= cushion:
                directionY = "BT"
            track_result = np.append(track_result,  [[vidPath, directionX, directionY]], axis=0)
        return track_result[1:,]
    return []



