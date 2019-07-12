import argparse
import cv2
import numpy as np

import bbox

def create_boxes(boxes):
    """Takes a list of polygons of the form "x,y:x,y:..." as a string
    and turns it into a list of ROIs, formatted in the standard format
    (see bbox.py for the explanation of that format).
    """
    rois = []
    for box in boxes:
        rois.append(np.array(map(lambda x: map(int, x.split(',')),
                                 box.split(':'))).reshape((-1, 1, 2)))
    return rois

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('roifile',
                            type=str,
                            help='The ROI file to modify.')
    arg_parser.add_argument('-d', '--delete',
                            type=int,
                            action='append',
                            dest='delete',
                            help='Specify an ROI number to delete.')
    arg_parser.add_argument('-a', '--add',
                            type=str,
                            action='append',
                            dest='add',
                            help='Define an ROI to add, of the form '
                                 'x,y:x,y:... over the vertices.')
    arg_parser.add_argument('-m', '--merge-file',
                            type=str,
                            action='append',
                            dest='merge',
                            help='Insert all of the ROIs defined from a file '
                                 'into the current one.')
    args = arg_parser.parse_args()
    boxes = bbox.read_bboxes(args.roifile)
    boxes = [boxes[i] for i in range(len(boxes)) if i not in args.delete]
    if args.add:
        boxes += create_boxes(args.add)
    if args.merge:
        for f in args.merge:
            boxes += bbox.read_bboxes(f)
    bbox.save_rois(boxes, args.roifile)

if __name__ == '__main__':
    main()

