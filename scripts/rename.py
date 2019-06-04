from matplotlib import pyplot as plt
import matplotlib.image as mpimg
from ffsplit import *
import math
import glob, os
from constants import *
import argparse
import matplotlib.patches as patches
import re

def reNameAll(VID_DIR, colonyNum, boxRegion):
    c=0
    vids = glob.glob(DIRECTORY + VID_DIR + "*.mp4")
    vids.sort()
    
    for vidName in vids:
        command = "mv "+ vidName + " "+ DIRECTORY + "C"+colonyNum + boxRegion+"-seg"+str(c)+".mp4"
        c+=1
        os.system(command)


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--v',
                            dest = 'vid_dir',
                            type=str,
                            default="",
                            help='directory of the video files (colony1/,colony2/,colony3/)')
    arg_parser.add_argument('--c',
                            dest = 'colony_number',
                            type=str,
                            default="",
                            help='the colony number (1,2,3)')
    arg_parser.add_argument('--b',
                            dest = 'box_region',
                            type=str,
                            default="",
                            help='the box region (R,D,O)')
    args = arg_parser.parse_args()
    if args.vid_dir:
        VID_DIR = args.vid_dir.split(',')
    else:
        raise Exception('requires a directory of the video files')
    if args.colony_number:
        colonyNum = args.colony_number.split(',')
    else:
        raise Exception('requires the colony number corresponding to the video directory')
    if args.box_region:
        boxRegion = args.box_region.split(',')
    else:
        raise Exception('requires the box region corresponding to the video directory')
    if len(boxRegion) != len(VID_DIR) or len(boxRegion) != len(colonyNum)  or len(colonyNum) != len(VID_DIR):
        raise Exception('all parameters must be the same length')
    for i in range(len(VID_DIR)):
        reNameAll(VID_DIR[i], colonyNum[i], boxRegion[i])

if __name__== "__main__":
    main()
