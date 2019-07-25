import cv2
import os, os.path
import numpy as np
from math import cos, sin
import argparse

import bbox

def label_rois(
        video, roifile, outfile, draw_polys=True,
        insignificant_edges=False, draw_box=False):
    """Labels the RoIs found in roifile onto the first frame of the
    video and saves that into outfile.
    
    If draw_polys is True, then it will also draw the polygons within
    each ROI and label them.

    If insignificant_edges is True, then all edges are labeled in cyan.
    Otherwise, the unimportant edges are labeled in a darker blue to
    distinguish them.

    If draw_box is true, then it will draw a solid black box around the
    area which is cropped in the croprotate step. Othewise, only the ROI
    polygon is drawn and labeled.
    """
    if not os.path.isdir(os.path.dirname(os.path.abspath(outfile))):
        os.makedirs(os.path.dirname(os.path.abspath(outfile)))
    ret, frame = cv2.VideoCapture(video).read()
    if not ret:
        raise RuntimeError('Encountered problem reading frame from video.')
    boxes = bbox.read_bboxes(roifile)
    lines = []
    for i, box in enumerate(boxes)):
        if draw_box:
            pts = np.array(box.box_vertices, np.int64)
            lines.append(pts.reshape((-1, 1, 2)))
        verts = box.poly_abspos
        if draw_polys:
            cv2.polylines(frame, [np.array(verts, np.int64).reshape((-1,1,2))],
                          True, (0,)*3, thickness=2)
            for j in range(-1, len(verts)-1):
                x = round((verts[j][0] +verts[j+1][0])/2) - 10
                y = round((verts[j][1] + verts[j+1][1])/2) + 15
                label = j % len(verts)
                if label in box.edges:
                    # Note: (200,200,0) is cyan. OpenCV uses BGR instead of RGB.
                    cv2.putText(frame, str(label), (x, y),
                                cv2.FONT_HERSHEY_PLAIN, 2, (200, 200, 0),
                                2, cv2.LINE_AA)
                else:
                    if insignificant_edges:
                        # If still drawing insignificant vertices, make them
                        # a darker blue to distinguish the real ones.
                        cv2.putText(frame, str(label), (x, y),
                                    cv2.FONT_HERSHEY_PLAIN, 2, (200, 0, 0),
                                    2, cv2.LINE_AA)
        x, y = box.center
        cv2.putText(frame, str(i), (x-10, y), cv2.FONT_HERSHEY_PLAIN,
                     3, (0,)*3, 2, cv2.LINE_AA)
    cv2.polylines(frame, lines, True, (0, 0, 0), thickness=3)
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
    args.add_argument('-i', '--draw-insignificant',
                      dest='insig',
                      action='store_true',
                      help='If specified, all edges are labeled. Otherwise, '
                           'only significant edges are labeled.')
    args = args.parse_args()
    label_rois(args.video, args.roifile, args.outfile,
               insignificant_edges=args.insig)

if __name__ == '__main__':
    main()

