import os, os.path
import argparse
import re
import math
import numpy as np

import bbox

def dist(x1, y1, x2, y2, x3, y3): # x3,y3 is the point
    px = x2-x1
    py = y2-y1

    norm = px*px + py*py

    u =  ((x3 - x1) * px + (y3 - y1) * py) / float(norm)

    if u > 1:
        u = 1
    elif u < 0:
        u = 0

    x = x1 + u * px
    y = y1 + u * py

    dx = x - x3
    dy = y - y3

    # Note: If the actual distance does not matter,
    # if you only want to compare what this function
    # returns to other results of this function, you
    # can just return the squared distance instead
    # (i.e. remove the sqrt) to gain a little performance

    dist = (dx*dx + dy*dy)**.5

    return dist


def convert(infile, outfile, bboxes, Dict):
    """Loads infile and converts it to which edges were crossed, as
    defined by the bboxes parameter, and then saves it to outfile.
    """
    if not os.path.isdir(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))
    verts = [np.array(bboxes[i].poly_relpos)
             for i in range(len(bboxes))]
    inp = open(infile)
    lines = inp.readlines()
    outp = open(outfile, 'w')
    outp.write('roi,id,edge0,x0,y0,t0,edge1,x1,y1,t1,number_warning,broken_track\n')

    for line in lines:
        # Find ROI number based on input filename
        roi, idnum, x0, y0, t0, x1, y1, t1, warning, brokentrack = line.strip().split(',')
        roi = roi[roi.find("ROI"):]
        num = int(re.search(r'([0-9]{1,2})+', roi).group(0))
        roinum = Dict[num]
        x0, y0, t0, x1, y1, t1 = map(float, (x0, y0, t0, x1, y1, t1))

        # Only consider the distance for relevant edges where crossings occur -- in this case,
        # only edges 1,3,5 are edges where ants walk across
        roi_verts = verts[roinum]
        roi_verts = np.roll(roi_verts, -1, axis = 0)
        segments = np.array([[roi_verts[i], roi_verts[i+1]] for i in range(0, len(roi_verts)-1, 2)])

        # Find closest edge where ant entered/exited
        min0 = 100000
        min1 = 100000
        index0 = None
        index1 = None
        for i in range(len(segments)):
            dist0=dist(segments[i][0][0], segments[i][0][1], segments[i][1][0], segments[i][1][1], x0, y0)
            dist1=dist(segments[i][0][0], segments[i][0][1], segments[i][1][0], segments[i][1][1], x1, y1)
            if dist0 < min0:
                min0 = dist0
                index0 = i
            if dist1 < min1:
                min1 = dist1
                index1 = i
        
        # Map edge number to a name
        Map = {0: "Base", 1: "Left", 2: "Right"}
        e0 = Map[index0]
        e1 = Map[index1]

        # If an ant track doesn't have a clear entrance/exit edge, mark track as broken
        if (min0 > 12) or (min1 > 12):
            brokentrack = 1
        outp.write(','.join(map(
            str,
            [roi, idnum, e0, x0, y0, t0, e1, x1, y1, t1, warning, brokentrack]
        )))
        outp.write('\n')
    outp.close()

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('infile',
                            type=str,
                            help='The file to read data in from.')
    arg_parser.add_argument('outfile',
                            type=str,
                            help='The file to which to write the output.')
    arg_parser.add_argument('roifile',
                            type=str,
                            help='The file from which to load the ROIs.')
    args = arg_parser.parse_args()
    rois = bbox.read_bboxes(args.roifile)
    Dict = {42:0, 122:1, 121:2, 41:3, 12:4, 40:5, 112:6, 8:7, 11:8, 6:9, 10:10, 4:11, 111:12, 2:13, 60:14, 0:15, 1:16, 3:17, 20:18, 7:19, 5:20, 211:21, 31:22, 21:23, 22:24, 30:25, 50:26, 212:27, 222:28, 221:29, 32:30}
    convert(args.infile, args.outfile, rois, Dict)

if __name__ == '__main__':
    main()

