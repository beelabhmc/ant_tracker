import cv2
import os, os.path
import numpy as np
from math import cos, sin
import argparse

import bbox

def label_rois(video, roifile, outfile):
    """Labels the RoIs found in roifile onto the first frame of the
    video and saves that into outfile.
    """
    if not os.path.isdir(os.path.dirname(os.path.abspath(outfile))):
        os.makedirs(os.path.dirname(os.path.abspath(outfile)))
    ret, frame = cv2.VideoCapture(video).read()
    if not ret:
        raise RuntimeError('Encountered problem reading frame from video.')
    boxes = bbox.read_bboxes(roifile)
    lines = []
    for i in range(len(boxes)):
        box = boxes[i]
        pts = np.array(bbox.get_box_vertices(box), np.int64)
        lines.append(pts.reshape((-1, 1, 2)))
        cv2.putText(frame, str(i), bbox.get_center(box), cv2.FONT_HERSHEY_PLAIN,
                    2, (0,)*3, 2)
    cv2.polylines(frame, lines, True, (0, 0, 0), thickness=2)
    cv2.imwrite(outfile, frame)

def main():
    args = argparse.ArgumentParser()
    args.add_argument('video',
                      type=str,
                      help='The video on which to draw the RoIs.'
                     )
    args.add_argument('roifile',
                      type=str,
                      help='The file from which to read the RoIs'
                     )
    args.add_argument('outfile',
                      type=str,
                      help='The file to which to write the output.'
                     )
    args = args.parse_args()
    label_rois(args.video, args.roifile, args.outfile)

if __name__ == '__main__':
    main()

