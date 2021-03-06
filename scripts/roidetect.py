import cv2
import numpy as np
import os.path
import os
import itertools
import argparse
from math import sin, cos, pi

import constants
import bbox
from convexify import convexify

def find_red(rgb, hue_diff, min_saturation, min_value):
    """Finds the red regions in the given image.
    
    rgb is the image to search, stored in the format made by cv2.imread
    by default.

    The three optional arguments represent the amount of tolerance for
    off-red colors in the image.
    """
    hsv = cv2.cvtColor(rgb, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([0, min_saturation, min_value]),
                            np.array([hue_diff, 255, 255]))
    mask += cv2.inRange(hsv,
                        np.array([180-hue_diff, min_saturation, min_value]),
                        np.array([180, 255, 255]))
    # To make it look for blue, check if the hue is within hue_diff of 120
    # Prof. Donaldson and I (Jarred) discussed trying blue rectangles
    # instead of red to reduce confusion between nests and polygons and
    # hopefully make the ROI detection clearer.
    return mask // 255

def smooth_regions(mask, open, dilate, close):
    """Removes random dots that get made, dilates existing regions, then
    mergers together regions which are very near each other
    """
    open_kernel = np.ones((open, open), np.uint8)
    dilate_kernel = np.ones((dilate, dilate), np.uint8)
    close_kernel = np.ones((close, close), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, open_kernel)
    mask = cv2.dilate(mask, dilate_kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, close_kernel)
    return mask

def find_polygons(mask, epsilon, top_level, has_child):
    """Takes the given mask and finds a polygon that fits it well.
    
    If top_level is  specified and falsy, then it will return all
    polygons in the image. Otherwise, it will return only the polygons
    which are "top-level", which is to say, not contained inside of
    another polygon.
    Because of the way contour detection works, if top_level is set to
    false, then any hollow polygons appear twice: once on their external
    perimeter and once in their internal.
    
    If has_child is specified and falsy, then it will return all
    polygons; otherwise, it will return only polygons which have a
    contour detected inside of them (i.e. are hollow).

    epsilon is a parameter specifying how loosely the polygon is allowed
    to fit the mask. The greater the value of epsilon, the fewer sides
    the resulting polygons will have.
    """
    contours, h = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    #polys = [cv2.approxPolyDP(contours[i], cv2.arcLength(contours[i], True) \
                 #* epsilon, True)
             #for i in range(len(contours))
             #if (not top_level or h[0][i][3] < 0) \
                     #and (not has_child or h[0][i][2] >= 0)
            #]
    return [contours[i] for i in range(len(contours))
            if (not top_level or h[0][i][3] < 0) \
               and (not has_child or h[0][i][2] >= 0)
           ]

def refine_polygon_skeleton(mask, poly, padding=6, epsilon=0.021):
    """Refine the polygon selection by converting into a skeleton and
    then taking the polygon of that.
    """
    x, y, w, h = cv2.boundingRect(poly)
    x0, x1 = max(0, x-padding), min(mask.shape[1], x+padding+w)
    y0, y1 = max(0, y-padding), min(mask.shape[0], y+padding+h)
    crop = np.array(mask[y0:y1, x0:x1])
    skel = np.zeros(crop.shape, np.uint8)
    elem = cv2.getStructuringElement(cv2.MORPH_CROSS, (5, 5))
    while cv2.countNonZero(crop):
        eroded = cv2.erode(crop, elem)
        opened = cv2.dilate(eroded, elem)
        skel |= crop - opened
        crop = eroded
    skel = cv2.dilate(skel,np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]],np.uint8))
    cnts, h = cv2.findContours(skel, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnts = [cnts[i] for i in range(len(cnts))
            if h[0][i][3] < 0 and h[0][i][2] >= 0]
    if not cnts:
        # Couldn't make it better through a skeleton
        print('Refining via skeleton failed.')
        return cv2.approxPolyDP(poly, cv2.arcLength(poly, True)*epsilon, True)
    cnt = max(cnts, key=lambda x: cv2.arcLength(x, True))
    poly = cv2.approxPolyDP(cnt, cv2.arcLength(cnt, True)*epsilon, True)
    poly += np.array([x0, y0])
    return poly

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
    arg_parser.add_argument('-f', '--frame',
                            dest='frame',
                            type=int,
                            default=1,
                            help='The frame number in the video to use for '
                                 'ROI detection (default=1)',
                           )
    arg_parser.add_argument('-u', '--hue-tolerance',
                            dest='hue',
                            type=int,
                            default=constants.HSV_HUE_TOLERANCE,
                            help='The tolerance for changing hue away from '
                                 'pure red, default '
                                 f'{constants.HSV_HUE_TOLERANCE}')
    arg_parser.add_argument('-s', '--min-saturation',
                            dest='sat',
                            type=int,
                            default=constants.HSV_SAT_MINIMUM,
                            help='The minimum saturation value allowed to be '
                                 f'red, defult {constants.HSV_SAT_MINIMUM}')
    arg_parser.add_argument('-v', '--min-value',
                            dest='val',
                            type=int,
                            default=constants.HSV_SAT_MINIMUM,
                            help='The minimum value allowed to be '
                                 f'red, defult {constants.HSV_VALUE_MINIMUM}')
    arg_parser.add_argument('-o', '--open-size',
                            dest='open',
                            type=int,
                            default=constants.SMOOTH_OPEN_SIZE,
                            help='The size by which to "open" the mask '
                                 'to remove small details, default '
                                 f'{constants.SMOOTH_OPEN_SIZE}')
    arg_parser.add_argument('-d', '--dilate-size',
                            dest='dilate',
                            type=int,
                            default=constants.SMOOTH_DILATE_SIZE,
                            help='The amount by which to dilate the mask, '
                                 f'default {constants.SMOOTH_DILATE_SIZE}')
    arg_parser.add_argument('-c', '--close-size',
                            dest='close',
                            type=int,
                            default=constants.SMOOTH_CLOSE_SIZE,
                            help='The amount by which to "close" the mask, '
                                 'filling in small holes, default '
                                 f'{constants.SMOOTH_CLOSE_SIZE}')
    arg_parser.add_argument('-e', '--poly-epsilon',
                            dest='epsilon',
                            type=float,
                            default=constants.POLYGON_EPSILON,
                            help='The amount of wiggle-room in defining '
                                 'the polygons from the contours, default '
                                 f'{constants.POLYGON_EPSILON}')
    arg_parser.add_argument('-p', '--bbox-padding',
                            dest='padding',
                            type=int,
                            default=constants.ROI_BBOX_PADDING,
                            help='The amount of padding around the polygon '
                                 'to include in the ROI, default '
                                 f'{constants.ROI_BBOX_PADDING}')
    arg_parser.add_argument('--include-children',
                            dest='top_level',
                            default=True,
                            const=False,
                            action='store_const',
                            help='If specified, include child contours as '
                                 'polygons. Otherwise, only top-level '
                                 'contours are interpreted as polygons.')
    arg_parser.add_argument('--include-barren',
                            dest='has_child',
                            default=True,
                            const=False,
                            action='store_const',
                            help='If specified, allow contours which lack '
                                 'children as polygons. Otherwise, only '
                                 'contours which have children count.')
    arg_parser.add_argument('--allow-concave',
                            dest='force_convex',
                            default=True,
                            const=False,
                            action='store_const',
                            help='If specified, allow concave ROI polygons. '
                                 'Otherwise, ROI polygons are forced to be '
                                 'convex.')
    args = arg_parser.parse_args()
    if not os.path.isfile(args.video):
        arg_parser.error(f'{args.video} is not a valid file.')
    video = cv2.VideoCapture(args.video)
    for i in range(args.frame-1):
        if not video.read()[0]:
            arg_parser.error(f'The video only has {i} frames.')
    ret, frame = video.read()
    if not ret:
        arg_parser.error('The video only has {} frames.'.format(args.frame-1))
    mask = find_red(frame, args.hue, args.sat, args.val)
    mask = smooth_regions(mask, args.open, args.dilate, args.close)
    polys = find_polygons(mask, args.epsilon, args.top_level, args.has_child)
    polys = [refine_polygon_skeleton(mask, poly, epsilon=args.epsilon)
             for poly in polys]
    if args.force_convex:
        polys = [convexify(poly) for poly in polys]
    rois = [bbox.BBox.from_verts(poly, args.padding) for poly in polys]
    bbox.save_rois(rois, args.outfile)

if __name__ == '__main__':
    main()

