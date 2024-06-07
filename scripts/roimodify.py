#!/usr/local/bin/python3.7

import argparse
import cv2
import numpy as np

import bbox

def create_boxes(boxes, args):
    """Takes a list of polygons of the form "x,y:x,y:..." as a string
    and turns it into a list of ROIs, formatted in the standard format
    (see bbox.py for the explanation of that format).
    """
    for box in args.create:
        boxes.append(bbox.BBox.from_verts(
            np.array(list(map(lambda x: [int(i) for i in x.split(',')],
                              box.split(':')))).reshape((-1, 1, 2)),
            2
        ))
    return boxes

def merge_boxes(boxes, args):
    """Takes a list of files and loads all of the ROIs from them and
    adds all of them to boxes.
    """
    for f in args.merge:
        boxes.extend(bbox.read_bboxes(f))
    return boxes

def delete_boxes(boxes, args):
    """Takes a list of boxes and returns a new list of boxes which has
    removed the boxes at indices specified by delete.
    """
    return [boxes[i] for i in range(len(boxes)) if i not in args.delete]

def replace_boxes(boxes, args):
    """Takes a list of boxes and returns a new list of boxes which has
    replaces the boxes at indices specified by replace with boxes 
    contained in the file specified by replacefile.
    """

    i,filename = args.replace
    boxes[int(i)] = bbox.read_bboxes(filename)[0]
    return boxes 

def important_edges(boxes, args):
    """Updates boxes by defining important edges."""
    for term in args.edges:
        roinum, edgelist = term.split(':')
        boxes[int(roinum)].edges = list(map(int, edgelist.split(',')))
    return boxes

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('roifile',
                            type=str,
                            help='The ROI file to modify.')
    subcommands = arg_parser.add_subparsers();
    delete = subcommands.add_parser('delete', help='Delete existing ROIs.')
    delete.add_argument('delete',
                        type=int, 
                        nargs='*',
                        help='The ROI(s) to delete.')
    delete.set_defaults(func=delete_boxes);
    replace = subcommands.add_parser('replace', help='Replace existing ROIs.')
    replace.add_argument('replace',
                        type=str, 
                        nargs='*',
                        help='The ROI number to replace and the filename to read a new ROI from.')
    replace.set_defaults(func=replace_boxes);
    # replacefile = subcommands.add_parser('replacefile', help='To be used with replace.')
    # replacefile.add_argument('replacefile',
    #                     type=str, 
    #                     nargs='*',
    #                     help='File containing new ROIs to replace old ROIs')
    create = subcommands.add_parser('add', help='Create new ROIs.')
    create.add_argument('create',
                        type=str,
                        nargs='*',
                        help='Define the ROIs to add, each of the form '
                             'x,y:x,y:... over all vertices in order.')
    create.set_defaults(func=create_boxes);
    merge = subcommands.add_parser('merge', help='Merge ROIs in another file.')
    merge.add_argument('merge',
                       type=str,
                       nargs='*',
                       help='List the files containing ROIs to merge.')
    merge.set_defaults(func=merge_boxes);
    edges = subcommands.add_parser('edges', help='Specify important edges.')
    edges.add_argument('edges',
                       type=str,
                       nargs='*',
                       help='List of important edges, formatted as '
                            '"ROI_NUM:EDGE1,EDGE2,..."')
    edges.set_defaults(func=important_edges)
    args = arg_parser.parse_args()
    boxes = bbox.read_bboxes(args.roifile)
    boxes = args.func(boxes, args)
    bbox.save_rois(boxes, args.roifile)

if __name__ == '__main__':
    main()

