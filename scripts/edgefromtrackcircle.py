import os, os.path
import argparse
import re
import math
import numpy as np

import bbox

import cv2


def on_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        coord = (x, y)
        cv2.destroyAllWindows()

        return coord
    
def crossed_circle(cx, cy, r, x0, y0, x1, y1):
    d0 = math.hypot(x0 - cx, y0 - cy)
    d1 = math.hypot(x1 - cx, y1 - cy)
    return (d0 < r and d1 > r) or (d0 > r and d1 < r)


def circle_region(cx, cy, x, y):
    angle = math.degrees(math.atan2(y - cy, x - cx)) % 360

    if 0 <= angle < 90:
        return 0
    elif 90 <= angle < 180:
        return 1
    elif 180 <= angle < 270:
        return 2
    else:
        return 3


def convert(infile, outfile, center, radius):

    if not os.path.isdir(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile), exist_ok=True)

    cx, cy = center

    with open(infile) as inp, open(outfile, 'w') as outp:
        outp.write(
            'roi,id,edge0,x0,y0,t0,edge1,x1,y1,t1,number_warning,broken_track\n'
        )

        for line in inp:
            roi, idnum, x0, y0, t0, x1, y1, t1, warning, brokentrack = \
                line.strip().split(',')

            roi = roi[roi.find("ROI"):]
            x0, y0, t0, x1, y1, t1 = map(float, (x0, y0, t0, x1, y1, t1))
            brokentrack = int(brokentrack)

            if crossed_circle(cx, cy, radius, x0, y0, x1, y1):

                d0 = math.hypot(x0 - cx, y0 - cy)
                d1 = math.hypot(x1 - cx, y1 - cy)

                if d0 > radius:
                    entry = circle_region(cx, cy, x0, y0)
                    exit = circle_region(cx, cy, x1, y1)
                else:
                    entry = circle_region(cx, cy, x1, y1)
                    exit = circle_region(cx, cy, x0, y0)
            else:
                entry = None
                exit = None
                brokentrack = 1

            Map = {
                0: "Right",
                1: "Top",
                2: "Left",
                3: "Bottom",
                None: "None"
            }

            e0 = Map[entry]
            e1 = Map[exit]

            outp.write(','.join(map(
                str,
                [roi, idnum, e0, x0, y0, t0, e1, x1, y1, t1, warning, brokentrack]
            )))
            outp.write('\n')

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

    # add argument for image file
    img = cv2.imread('placeholder_img.png', 1)
    cv2.imshow('image', img)
    center_coord = cv2.setMouseCallback('image', on_mouse)

    # I haven't tested this radius value, so fear free to check it
    convert(args.infile, args.outfile, center_coord, radius=5)

if __name__ == '__main__':
    main()

