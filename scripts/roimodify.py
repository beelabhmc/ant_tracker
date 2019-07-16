import argparse
import cv2
import numpy as np

import bbox

def create_boxes(boxes, newboxes):
    """Takes a list of polygons of the form "x,y:x,y:..." as a string
    and turns it into a list of ROIs, formatted in the standard format
    (see bbox.py for the explanation of that format).
    """
    for box in newboxes:
        boxes.append(bbox.convert_polygon_to_roi(
            np.array(list(map(lambda x: [int(i) for i in x.split(',')],
                              box.split(':')))).reshape((-1, 1, 2)),
            2
        ))
    return boxes

def merge_boxes(boxes, files):
    """Takes a list of files and loads all of the ROIs from them and
    adds all of them to boxes.
    """
    for f in files:
        boxes.extend(bbox.read_bboxes(f))
    return boxes

def delete_boxes(boxes, nums):
    """Takes a list of boxes and returns a new list of boxes which has
    removed the boxes at indices specified by nums.
    """
    return [boxes[i] for i in range(len(boxes)) if i not in nums]

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('roifile',
                            type=str,
                            help='The ROI file to modify.')
    subcommands = arg_parser.add_subparsers();
    delete = subcommands.add_parser('delete', help='Delete existing ROIs.')
    delete.add_argument('input',
                        type=int, 
                        nargs='*',
                        help='The ROI(s) to delete.')
    delete.set_defaults(func=delete_boxes);
    create = subcommands.add_parser('add', help='Create new ROIs.')
    create.add_argument('input',
                        type=str,
                        nargs='*',
                        help='Define the ROIs to add, each of the form '
                             'x,y:x,y:... over all vertices in order.')
    create.set_defaults(func=create_boxes);
    merge = subcommands.add_parser('merge', help='Merge ROIs in another file.')
    merge.add_argument('input',
                       type=str,
                       nargs='*',
                       help='List the files containing ROIs to merge.')
    merge.set_defaults(func=merge_boxes);
    args = arg_parser.parse_args()
    boxes = bbox.read_bboxes(args.roifile)
    boxes = args.func(boxes, args.input)
    bbox.save_rois(boxes, args.roifile)

if __name__ == '__main__':
    main()

