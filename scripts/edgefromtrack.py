import os, os.path
import argparse
import re
import math
import numpy as np

import bbox

def find_floor_angle(angles, target_angle):
    """Takes a list of angles and returns the angle in that list which
    is closest counterclockwise of the given angle, as a (index, value)
    tuple.

    This is used to find which edge is crossed in the convert function.
    """
    curr = -1, 100
    for index, angle in enumerate(angles[1:], 1):
        if angle < curr[1] and angle >= target_angle:
            curr = index, angle
    if curr[0] == -1:
        m = min(angles)
        return angles.index(m), m
    return curr

def convert(infile, outfile, bbox):
    """Loads infile and converts it to which edges were crossed, as
    defined by the bboxes parameter, and then saves it to outfile.
    """
    if not os.path.isdir(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))
    center = np.array(bbox[1])/2
    verts = np.array(bbox.get_poly_relpos(bbox))-center
    offset = math.atan2(verts[0][1], verts[0][0]) % (2*math.pi)
    angles = [round((math.atan2(vert[1], vert[0])-offset) % (2*math.pi), 3)
              for vert in verts]
    inp = open(infile)
    outp = open(outfile, 'w')
    outp.write('filename,idnum,edge0,t0,edge1.t1\n')
    for line in inp:
        filename, idnum, x0, y0, t0, x1, y1, t1, number_warning = line.split(',')
        x0 -= center[0]
        y0 -= center[1]
        x1 -= center[0]
        y1 -= center[1]
        a0 = (math.atan2(y0, x0) - offset) % (2*math.pi)
        a1 = (math.atan2(y1, x1) - offset) % (2*math.pi)
        edge0 = -1
        edge1 = -1
        outp.write('%s\n' % ','.join(filename, idnum, edge0, t0, edg1, t1))
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
    convert(args.infile, args.outfile, rois)

if __name__ == '__main__':
    main()

