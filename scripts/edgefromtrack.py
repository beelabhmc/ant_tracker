import os, os.path
import argparse
import re
import math
import numpy as np

import bbox

class Interval:
    """A class for storing an interval of angles."""
    def __init__(self, floor, ceil, payload=None):
        """Create a new interval with lower bound floor and upper bound
        ceil.

        If specified, payload is just extra optional data that it can
        hold. I use it to store the edge number.
        """
        self.floor = floor
        self.ceil = ceil
        self.payload = payload

    def contains(self, value):
        """Returns true iff value is between self.floor and self.ceil"""
        if self.floor < self.ceil:
            return self.floor < value and self.ceil > value
        else:
            return self.floor < value or self.ceil > value

    def distance(self, value, modulus=2*math.pi):
        """Returns the distance from value to this interval, under the
        given modulus.
        """
        if self.contains(value):
            return 0
        else:
            floordist = self.floor - value
            if floordist < 0:
                floordist += modulus
            ceildist = value - self.ceil
            if ceildist < 0:
                ceildist += modulus
            return min(floordist, ceildist)

    def __repr__(self):
        return 'Interval({},{},{})'.format(self.floor, self.ceil, self.payload)

def closest_interval(value, intervals, modulus=2*math.pi):
    """Given a value, a list of intervals, and a modulus, it returns
    the closest interval in the list to the given value.
    """
    closest = (None, modulus*2)
    for interval in intervals:
        distance = interval.distance(value, modulus)
        if distance < closest[1]:
            closest = interval, distance
    return closest[0]

def to_edge(x, y, intervals, offset, center):
    x -= center[0]
    y -= center[1]
    angle = (math.atan2(y, x) - offset) % (2*math.pi)
    return closest_interval(angle, intervals).payload

def convert(infile, outfile, bboxes):
    """Loads infile and converts it to which edges were crossed, as
    defined by the bboxes parameter, and then saves it to outfile.
    """
    if not os.path.isdir(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))
    centers = [np.array([box.w/2, box.h/2]) for box in bboxes]
    verts = [np.array(bboxes[i].poly_relpos)-centers[i]
             for i in range(len(bboxes))]
    offsets = [math.atan2(verts[i][0][1], verts[i][0][0]) % (2*math.pi)
               for i in range(len(verts))]
    angles = [[round((math.atan2(vert[1], vert[0])-offsets[i]) % (2*math.pi), 3)
               for vert in verts[i]] for i in range(len(verts))]
    intervals = []
    for i, box in enumerate(bboxes):
        box_intervals = []
        for edge in box.edges:
            box_intervals.append(Interval(
                angles[i][(edge+1) % len(angles[i])],
                angles[i][edge],
                edge
            ))
        intervals.append(box_intervals)
    inp = open(infile)
    outp = open(outfile, 'w')
    outp.write('roi,id,edge0,x0,y0,t0,edge1,x1,y1,t1,number_warning\n')
    for line in inp:
        roi, idnum, x0, y0, t0, x1, y1, t1, warning = line.strip().split(',')
        roinum = int(re.search(r'[0-9]+', roi).group(0))
        x0, y0, t0, x1, y1, t1 = map(float, (x0, y0, t0, x1, y1, t1))
        e0 = to_edge(x0, y0, intervals[roinum],
                     offsets[roinum], centers[roinum])
        e1 = to_edge(x1, y1, intervals[roinum],
                     offsets[roinum], centers[roinum])
        outp.write(','.join(map(
            str,
            [roi, idnum, e0, x0, y0, t0, e1, x1, y1, t1, warning]
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
    convert(args.infile, args.outfile, rois)

if __name__ == '__main__':
    main()

