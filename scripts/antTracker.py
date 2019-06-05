from __future__ import division
import math
import glob
import os
import argparse
import re
import numpy as np
import cv2
import subprocess

import constants
import split
from track import *
import vid_meta_data as metadata

def getBBox(ROI_fileName):
    """read ROI labels from txt into a dictionary dict keys will be
    tuples containing
        1) the path to the frame that was used
        2) the ROI label name
    dict values will be lists containing the coords of the box
    """
    bboxes={}
    f = open(constants.DIRECTORY+ROI_fileName, 'r')
    # get the ROI label names (separated by tabs)
    names = f.readline().strip().split("\t")[1:]
    names = [re.sub("_1", "", x) for x in names]
    c=0
    for line in f:
        # get ROI coords and path to frame
        line = line.strip().split("\t")
        print(line)
        filePath = line[0].split('.')[0]
        numbers = line[1:]
        numbers = [int(x) if x else None for x in numbers]
        nums = len(numbers)
        for i in range(0, nums//4):
            #if numbers[i]:
                # save filepath and ROI name as keys for the ROI coords
                bboxes[(filePath, names[i])] = numbers[i:nums:nums//4]
    f.close()
    return bboxes

def cropTimeAndSpace(BBoxDict, split_unused=False):
    """split videos into 10 min segments then crop into boxes
    according to the coordinates provided in ROI_fileName

    if split_unused is set to True, then it will split all videos;
    otherwise, only videos in BBoxDict will be split
    """
    # warn if user input is invalid
    if len(glob.glob(constants.VID_DIR + "*.mp4")) == 0:
        warnings.warn("couldn't find any video files for processing. do your "
                      "videos have a .mp4 extension? have you set VID_DIR in "
                      "constants.py?")
    # get paths to videos
    # to split videos by time
    print('Clearing split directory')
    subprocess.call(['rm', '-r', constants.DIRECTORY+constants.SPLIT_DIR])
    subprocess.call(['mkdir', constants.DIRECTORY+constants.SPLIT_DIR])
    vids = set(key[0].split('/')[-1] for key in BBoxDict.keys())
    boxNames = BBoxDict.keys()
    for vidName in glob.glob(constants.VID_DIR + "*.mp4"):
        if not split_unused and vidName.split('/')[-1].split('.')[0]not in vids:
            print("Skipping %s" % vidName)
            continue
        print("Splitting %s" % vidName)
        # create VideoCapture object
        vidcap = cv2.VideoCapture(vidName)
        # get colony ID (ex: C1D)
        vidName_pre = vidName.split("-")[0]
        # split videos into 600 sec segments each
        split.by_seconds(vidName, 600, extra = '-threads 8')
    # crop each video
    print('Clearing crop directory')
    subprocess.call(['rm', '-r', constants.DIRECTORY+constants.CROP_DIR])
    subprocess.call(['mkdir', constants.DIRECTORY+constants.CROP_DIR])
    for splitVid in glob.glob(constants.DIRECTORY+constants.SPLIT_DIR +"*.mp4"):
        # boxNm should be a tuple containing the absolute path to the
        # frame that was used, as well as the ROI label name
        for boxNm in boxNames:
            # if splitVid has the same colony ID as boxNm
            if (boxNm[0].split('/')[-1]).split("-")[0] \
                    == (splitVid.split('/')[-1]).split("-")[0]:
                # get the coords for this box
                boxCoord = BBoxDict[boxNm]
                x = float(boxCoord[0])
                y = float(boxCoord[1])
                w = boxCoord[2]
                h = boxCoord[3]
                # call ffmpeg with the coords to actually do the work
                # of cropping the video
                rectangle = str(w) +':' + str(h) +':' + str(x) +':'+ str(y) 
                cropName = constants.DIRECTORY + constants.CROP_DIR \
                           + (splitVid.split("/")[-1]).split(".")[0] + "-" \
                           + str(boxNm[-1]).replace(' ', '') +".mp4"
                print("Attempting to create cropped output: " + cropName)
                # this uses a simple filtergraph to crop the video (type
                # "man ffmpeg" in the terminal for more info)
                # we use the -y option to force overwrites of output files
                command = 'ffmpeg -y -i ' + splitVid +' -vf "crop='+rectangle \
                          + '" '+ cropName+' >>'+constants.DIRECTORY + \
                          'log.txt 2>&1'
                os.system(command)


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('ROI',
                            type=str,
                            default="",
                            help='a txt file of the bounding boxes for ROI')
    arg_parser.add_argument('--c',
                            dest = 'cushion',
                            type=int,
                            default=constants.PADDING,
                            help='number of pixels as padding (default = '
                                 '%d)' % constants.PADDING)
    arg_parser.add_argument('--m',
                            dest = 'minBlob',
                            type=int,
                            default=constants.MIN_BLOB,
                            help='minimum blob area in pixels (default = '
                                 '%d)' % constants.MIN_BLOB)
    arg_parser.add_argument('--e',
                            dest = 'export',
                            type=bool,
                            default=False,
                            help='do we export result video (default = False)')

    args = arg_parser.parse_args()
    if args.ROI:
        ROIFile = args.ROI
    else:
        raise Exception('requires a txt file of the bounding boxes for ROI')
    if args.cushion:
        cushion =  args.cushion
    else:
        cushion = constants.PADDING
    if args.minBlob:
        minBlob =  args.minBlob
    else:
        minBlob = constants.MIN_BLOB
    if args.export:
        export =  args.export
    else:
        export = True
    
    # clear the log file
    os.system("echo '' >"+constants.DIRECTORY+'log.txt')

    BBoxDict = getBBox(ROIFile)
    cropTimeAndSpace(BBoxDict)

    # track ants in each of the cropped videos
    result_array = np.array([['fName', 'id', 'X', 'Y']])
    for cropVid in glob.glob(constants.DIRECTORY+ constants.CROP_DIR +"*.mp4"):
        print("Tracking ants in " + cropVid)
        # get heigh and width of video
        H, W = metadata.get_video_dimensions(cropVid)
        result_path = constants.DIRECTORY + constants.RESULT_VID_DIR
        # call matlab to track ants in a single cropped video
        track_result = trackOneClip(cropVid, W, H, export, result_path, minBlob)
        # keep track of the tracking results in a np array
        if track_result:
            result_array = np.concatenate((result_array, track_result[0]),
                                          axis=0)
    print(result_array)
    # save the tracking results to disk
    np.savetxt(constants.DIRECTORY+"tracking_results.csv", result_array,
               delimiter= ',', fmt='%s')


if __name__== "__main__":
    main()
