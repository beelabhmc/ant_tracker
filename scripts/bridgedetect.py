import cv2
import matplotlib.pyplot as plt
import numpy as np

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

def smooth_regions(mask, open=3, dilate=5, close=9):
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

def find_rects(mask):
    """Takes a mask and returns bounding rectangles on the white areas."""
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    return list(map(cv2.minAreaRect, contours))

def pair_rects(rects):
    """Takes a list of rectangles and pairs them by centroid position."""
    out = []
    while rects:
        pos = sum(cv2.boxPoints(rects[0]))/8
        near = (len(rects), 1e100)
        for i in range(1, len(rects)):
            dist = np.sqrt(np.sum((sum(cv2.boxPoints(rects[i]))/8 - pos)**2))
            if dist < near[1]:
                near = i, dist
        # print(near, rects)
        out.append((rects[0], rects[near[0]]))
        rects = rects[1:near[0]]+rects[near[0]+1:]
    return out

rects = find_rects(smooth_regions(find_red(cv2.imread('../input/red-bridge.png'))))

