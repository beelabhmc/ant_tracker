import re
import cv2
import os, os.path
import argparse
import numpy as np

import bbox

def label_edges(video, roifile, outfile, roinum=None):
    """Label the edges of an ROI in a frame of a cropped video file.

    video is the path to a video of the cropped region.

    roifile is the file from which to take the ROIs.

    outfile is the file in which to save the output image.

    roinum is the number of the ROI. If unspecified, it tries to guess
    based on the name of the video, raising an error if it can't.
    """
    if not os.path.isfile(video):
        raise ValueError(f'Can\'t find file {video}.')
    if roinum is None:
        try:
            roinum = int(re.search(r'[0-9]+', os.path.basename(video)).group(0))
        except Exception as e:
            raise ValueError(f'Can\'t compute ROI number for {video}.') from e
    try:
        box = bbox.read_bboxes(roifile)[roinum]
        verts = bbox.get_poly_relpos(box)
        pts = np.array(verts, np.int64).reshape((-1, 1, 2))
    except Exception as e:
        raise RuntimeError(f'Error reading ROI file {roifile}.') from e
    ret, frame = cv2.VideoCapture(video).read()
    if not ret:
        raise RuntimeError(f'Unknown issue reading {video}.')
    # Draw the polygon edges
    cv2.polylines(frame, [pts], True, (0,)*3, thickness=2)
    # Now label them
    for i in range(-1, len(verts)-1):
        x = round((verts[i][0] + verts[i+1][0])/2) - 10
        y = round((verts[i][1] + verts[i+1][1])/2) + 15
        cv2.putText(frame, str(i%len(verts)), (x, y), cv2.FONT_HERSHEY_PLAIN,
                    2, (0,)*3, 2)
    if not os.path.isdir(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))
    cv2.imwrite(outfile, frame)

def main():
    args = argparse.ArgumentParser()
    args.add_argument('video',
                      type=str,
                      help='The cropped video onto which to label the edges.')
    args.add_argument('roifile',
                      type=str,
                      help='The file from which to load the ROI to draw.')
    args.add_argument('outfile',
                      type=str,
                      help='The file to which to write the video frame with '
                           'edges labeled.')
    args = args.parse_args()
    label_edges(args.video, args.roifile, args.outfile)

if __name__ == '__main__':
    main()

