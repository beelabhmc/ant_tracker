#import logging
import argparse

import numpy as np
from matplotlib import pyplot as plt
import cv2

from roipoly import RoiPoly
import bbox

# logging.basicConfig(format='%(levelname)s ''%(processName)-10s : %(asctime)s '
#                            '%(module)s.%(funcName)s:%(lineno)s %(message)s',
#                     level=logging.INFO)

def draw_roi(imgfile, newroifile, isRightHandJunction=False):
    
       # Load image
       img = cv2.imread(imgfile)

       # Show the image
       fig = plt.figure()
       plt.imshow(img, interpolation='nearest', cmap="Greys")
       plt.colorbar()
       plt.title("left click: line segment         right click or double click: close region")
       plt.show(block=False)

       # Let user draw first ROI
       roi1 = RoiPoly(color='r', fig=fig)

       # Show the image with the first ROI
       fig = plt.figure()
       plt.imshow(img, interpolation='nearest', cmap="Greys")
       plt.colorbar()
       roi1.display_roi()

       roi_coordinates = roi1.get_roi_coordinates()
       # print(roi_coordinates)


       # reorder coordinates so longest edge is first
       poly = np.array(roi_coordinates, int)
       d = np.diff(poly, axis=0, append=poly[0:1])
       segdists = np.sqrt((d ** 2).sum(axis=1))
       index = np.argmax(segdists)
       roll = np.roll(poly, -index, axis=0)

       # if it is a right-handed junction, reorder again so edge #1 is base
       if isRightHandJunction:
              roll = np.roll(roll, 2, axis=0)

       # calculate minimum bounding box and report in bbox format
       new_roi = [bbox.BBox.from_verts(roll, 3)]
       bbox.save_rois(new_roi, newroifile)

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('imgfile',
                            type=str,
                            help='The image file upon which to draw the new ROI.')
    arg_parser.add_argument('newroifile',
                            type=str,
                            help='The name of the file to write the new ROI to')
    arg_parser.add_argument('-r', "--rightHanded",
                            action="store_true",
                            help='specify if right-handed junction (left-handed is default)')
    args = arg_parser.parse_args()
    draw_roi(args.imgfile, args.newroifile, args.rightHanded)
    
if __name__ == '__main__':
    main()
