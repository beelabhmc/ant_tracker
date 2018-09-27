import cv2
import math
import glob, os
from constants import *
import argparse
import re

def saveFirstFrame(vidName):
    vidcap = cv2.VideoCapture(DIRECTORY+vidName)
    success,image = vidcap.read()
    vidNameShort = vidName.split(".")[0]
    cv2.imwrite(DIRECTORY+vidNameShort+".jpg", image) 



def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--f',
                            dest = 'vidFiles',
                            type=str,
                            default=[],
                            help='a comma separated list of inital .mp4 files')
    args = arg_parser.parse_args()
    if args.vidFiles:
        vidFiles=args.vidFiles.split(',')
    else:
        raise Exception('requires a comma separated list of inital .mp4 files')
    for vid in vidFiles:
        saveFirstFrame(vid)

if __name__== "__main__":
    main()
