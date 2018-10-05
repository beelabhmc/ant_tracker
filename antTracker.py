from ffsplit import *
import math
import glob, os
from constants import *
import argparse
import re
import numpy as np
import cv2
from track import *
from vid_meta_data import *

def getBBox(ROI_fileName):
    """
        read ROI labels from txt into a dictionary
        dict keys will be tuples containing
            1) the path to the frame that was used
            2) the ROI label name
        dict values will be lists containing the coords of the box
    """
    bboxes={}
    file = open(DIRECTORY+ROI_fileName, 'r')
    # get the ROI label names (separated by tabs)
    names = file.readline().strip().split("\t")[1:]
    names = [re.sub("_1", "", x) for x in names]
    c=0
    for line in file:
        # get ROI coords and path to frame
        line = line.strip().split("\t")
        filePath = line[0].split('.')[0]
        numbers = line[1:]
        numbers = [int(x) if x else None for x in numbers]
        for i in range(0, len(numbers), 4):
            if numbers[i]:
                # save filepath and ROI name as keys for the ROI coords
                bboxes[(filePath, names[i])] = numbers[i:(i+4)]
    file.close()
    return bboxes

def cropTimeAndSpace(BBoxDict):
    # get paths to videos
    for vidName in glob.glob(VID_DIR + "*.mp4"):
        # create VideoCapture object
        vidcap = cv2.VideoCapture(vidName)
        # get colony ID
        vidName_pre = vidName.split("-")[0]
        boxNames = BBoxDict.keys()
        # split videos into 600 sec segments each
        split_by_seconds(vidName, 600, extra = '-threads 8')
    for splitVid in glob.glob(DIRECTORY+ SPLIT_DIR +"*.mp4"):
        for boxNm in boxNames:
            if (boxNm[0].split('/')[-1]).split("-")[0] == (splitVid.split('/')[-1]).split("-")[0]:
                print((boxNm[0].split('/')[-1]).split("-")[0])
                print((splitVid.split('/')[-1]).split("-")[0])
                boxCoord = BBoxDict[boxNm]
                x = float(boxCoord[0])
                y = float(boxCoord[1])
                w = boxCoord[2]
                h = boxCoord[3]
                rectangle = str(w) +':' + str(h) +':' + str(x) +':'+ str(y) 
                cropName = DIRECTORY + CROP_DIR + (splitVid.split("/")[-1]).split(".")[0]+ "-" + str(boxNm[-1]) +".mp4"
                command = 'ffmpeg -i ' + splitVid +' -vf "crop=' + rectangle + '" '+ cropName
                os.system(command)


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--f',
                            dest = 'ROI',
                            type=str,
                            default="",
                            help='a txt file of the bounding boxes for ROI')
    arg_parser.add_argument('--c',
                            dest = 'cushion',
                            type=int,
                            default=10,
                            help='number of pixels as padding (default = 10)')
    arg_parser.add_argument('--m',
                            dest = 'minBlob',
                            type=int,
                            default=35,
                            help='minimum blob area in pixels (default = 35)')
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
        cushion = 10
    if args.minBlob:
        minBlob =  args.minBlob
    else:
        minBlob = 35
    if args.export:
        export =  args.export
    else:
        export = True
    
    BBoxDict = getBBox(ROIFile)
    cropTimeAndSpace(BBoxDict)

    result_array = np.array([["fName", "X", "Y"]])
    for cropVid in glob.glob(DIRECTORY+ CROP_DIR +"*.mp4"):
        print cropVid
        H, W = findVideoMetada(cropVid)
        result_path = DIRECTORY + RESULT_VID_DIR
        track_result = trackOneClip(cropVid, cushion, W, H, minBlob, export, result_path)
        if track_result !=[]:
            result_array = np.concatenate((result_array, track_result), axis=0)
    print(result_array)
    np.savetxt(DIRECTORY+"tracking_results.txt", result_array, delimiter= ',',  fmt='%s')
    np.savetxt(DIRECTORY+"tracking_results.csv", result_array, delimiter= ',', fmt='%s')




if __name__== "__main__":
    main()