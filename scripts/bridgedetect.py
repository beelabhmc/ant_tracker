import cv2
import numpy as np
import os.path
import itertools
import argparse
from math import sin, cos, pi

import constants

def find_red(rgb, hue_diff=constants.HSV_HUE_TOLERANCE,
             min_saturation=constants.HSV_SAT_MINIMUM,
             min_value=constants.HSV_VALUE_MINIMUM):
    """Finds the red regions in the given image.
    
    rgb is the image to search, stored in the format made by cv2.imread
    by default.

    The three optional arguments represent the amount of tolerance for
    off-red colors in the image.
    """
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, np.array([0, min_saturation, min_value]),
                            np.array([hue_diff, 255, 255]))
    mask+= cv2.inRange(hsv, np.array([180-hue_diff, min_saturation, min_value]),
                            np.array([180, 255, 255]))
    return mask // 255

def smooth_regions(mask, open=constants.SMOOTH_OPEN_SIZE,
                         dilate=constants.SMOOTH_DILATE_SIZE,
                         close=constants.SMOOTH_CLOSE_SIZE):
    """Removes random dots that get made, dilates existing regions, then
    mergers together regions which are very near each other
    """
    open_kernel = np.ones((open, open), np.uint8)
    dilate_kernel = np.ones((dilate, dilate), np.uint8)
    close_kernel = np.ones((close, close), np.uint8)
    return cv2.morphologyEx(cv2.dilate(cv2.morphologyEx(mask,
                                                        cv2.MORPH_OPEN,
                                                        open_kernel
                                                       ),
                                       dilate_kernel, iterations=2
                                      ),
                            cv2.MORPH_CLOSE, close_kernel
                           )

def find_polygons(mask, top_level=True, epsilon=constants.POLYGON_EPSILON):
    """Takes the given mask and finds a polygon that fits it well.
    
    If top_level is  specified and falsy, then it will return all
    polygons in the image. Otherwise, it will return only the polygons
    which are "top-level", which is to say, not contained inside of
    another polygon.
    Because of the way contour detection works, if
    top_level is set to false, then any hollow polygons appear twice:
    once on their external perimeter and once in their internal.

    epsilon is a parameter specifying how loosely the polygon is allowed
    to fit the mask. The greater the value of epsilon, the fewer sides
    the resulting polygons will have.
    """
    contours, h = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    polys = [cv2.approxPolyDP(contours[i], cv2.arcLength(contours[i], True) \
             * epsilon, True)
             for i in range(len(contours)) if not top_level or h[0][i][3] < 0]
    return polys

def convert_polygon_to_roi(poly):
    """Takes a polygon and outputs it in ROI format. This consists of a
    list in which the first item is a tuple with the x,y coordinates of
    the upper-left corner of the bounding rectangle, the second is a
    tuple specifying its length and width, and the third is its angle to
    the vertical in radians, between 0 and π/2, measured in radians. The
    fourth item is the polygon which was passed in.
    """
    (x, y), (w, h), angle = cv2.minAreaRect(poly)
    angle = pi/180 * (90+angle)  # Convert to quadrant 1 radians
    w, h = h, w  # swap width and height because angle is changed
    print(((x, y), (w, h), angle))
    x += -cos(angle)*w/2 + sin(angle)*h/2
    y += -sin(angle)*w/2 - cos(angle)*h/2
    x, y, w, h, angle = map(lambda x: round(x, 2), [x, y, w, h, angle])
    print(((x, y), (w, h), angle))
    return [(x, y), (w, h), angle, poly]

def flatten(lst):
    """Flattens a list by taking any iterable element of the list and
    expanding it to be a list of its own.
    """
    out = []
    for item in lst:
        try:
            iter(item)
            out += flatten(item)
        except TypeError:
            out.append(item)
    return out

def save_rois(rois, outfile, imagename, append=True):
    if os.path.exists(outfile) and append:
        f = open(outfile, 'a')
    else:
        f = open(outfile, 'w')
    rois = [','.join(map(str, flatten(roi))) for roi in rois]
    f.write('%s %s\n' % (imagename, ' '.join(rois)))
    f.close()

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('video',
                            type=str,
                            help='The path to a video with ROIs to detect.',
                           )
    arg_parser.add_argument('outfile',
                            type=str,
                            help='The path to a file in which to write the '
                                 'detected ROIs.',
                           )
    arg_parser.add_argument('-o', '--override',
                            dest='override',
                            action='store_const', const=False,
                            default=True,
                            help='Override the outfile if it already exists '
                                 '(default=append to the file)',
                           )
    arg_parser.add_argument('-f', '--frame',
                            dest='frame',
                            type=int,
                            default=1,
                            help='The frame number in the video to use for '
                                 'ROI detection (default=1)',
                           )
    args = arg_parser.parse_args()
    video = cv2.VideoCapture(args.video)
    for i in range(args.frame-1):
        if not video.read()[0]:
            arg_parser.error('The video only has %d frames.' % i)
    exists, frame = video.read()
    if not exists:
        arg_parser.error('The video only has %d frames.' % (args.frame-1))
    mask = smooth_regions(find_red(frame))
    rois = list(map(convert_polygon_to_roi, find_polygons(mask)))
    save_rois(rois, args.outfile, args.video, append=args.override)

if __name__ == '__main__':
    main()

