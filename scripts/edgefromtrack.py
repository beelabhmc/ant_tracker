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

def convert(infile, outfile, bboxes):
    """Loads infile and converts it to which edges were crossed, as
    defined by the bboxes parameter, and then saves it to outfile.
    """
    #TODO Consider box.edges edges only and not the other ones
    if not os.path.isdir(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))
    centers = [np.array([box.w/2, box.h/2]) for box in bboxes]
    verts = [np.array(bboxes[i].poly_relpos)-centers[i]
             for i in range(len(bboxes))]
    offsets = [math.atan2(verts[i][0][1], verts[i][0][0]) % (2*math.pi)
               for i in range(len(verts))]
    angles = [[round((math.atan2(vert[1], vert[0])-offsets[i]) % (2*math.pi), 3)
               for vert in verts[i]] for i in range(len(verts))]
    inp = open(infile)
    outp = open(outfile, 'w')
    outp.write('roi,id,edge0,t0,edge1,t1,number_warning\n')
    for line in inp:
        roi, idnum, x0, y0, t0, x1, y1, t1, warning = line.strip().split(',')
        roinum = int(re.search(r'[0-9]+', roi).group(0))
        x0, y0, t0, x1, y1, t1 = map(float, (x0, y0, t0, x1, y1, t1))
        x0 -= centers[roinum][0]
        y0 -= centers[roinum][1]
        a0 = (math.atan2(y0, x0) - offsets[roinum]) % (2*math.pi)
        e0 = find_floor_angle(angles[roinum], a0)[0]
        x1 -= centers[roinum][0]
        y1 -= centers[roinum][1]
        a1 = (math.atan2(y1, x1) - offsets[roinum]) % (2*math.pi)
        e1 = find_floor_angle(angles[roinum], a1)[0]
        outp.write(','.join(map(str, [roi, idnum, e0, t0, e1, t1, warning])))
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
    convert(args.infile, args.outfile, rois)

if __name__ == '__main__':
    main()

