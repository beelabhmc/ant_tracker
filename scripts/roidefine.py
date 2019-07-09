import cv2
import matplotlib.pyplot as plt
import numpy as np
import argparse
import os, os.path

import bbox

def roi_poly_input(video, show_image=False):
    if not os.path.isfile(video):
        raise RuntimeError(f'{video} is not a file.')
    if show_image:
        ret, img = cv2.VideoCapture(video).read()
        if not ret:
            raise RuntimeError(f'Unknown error reading {video}')
        plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        try:
            from roipoly import MultiRoi
        except ImportError:
            print('Module roipoly is not installed, using backup method.')
            plt.draw()
        else:
            # Only run this code if roipoly can be imported
            rois = list(MultiRoi().rois.values())
            rois = [list(zip(r.x, r.y)) for r in rois]
            rois = [np.array(roi, np.int32).reshape((-1, 1, 2)) for roi in rois]
            return [bbox.convert_polygon_to_roi(roi, 2) for roi in rois]
    num_rois = int(input('How many ROIs are in this video? '))
    rois = []
    for i in range(num_rois):
        pts = []
        prompt = 'Please input x,y coordinates of the next point, separated ' \
                 'by a comma, or an empty string to save this ROI.'
        while True:
            line = input(prompt)
            if line == '':
                break
            try:
                x, y = map(float, line.split(','))
                pts.append((x, y))
            except:
                print('Could not read input. Please try again.')
                continue
        box = bbox.convert_poly_to_roi(np.array(pts).reshape((-1, 1, 2)), 2)
        rois.append(box)
    return rois

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('infile',
                            type=str,
                            help='The path to the video to read.')
    arg_parser.add_argument('outfile',
                            type=str,
                            help='The file to which to write the rois.')
    arg_parser.add_argument('--no-polys',
                            default=False,
                            const=True,
                            action='store_const',
                            help='Do not input polygons, only rectangular '
                                 'bboxes.')
    args = arg_parser.parse_args()
    rois = roi_poly_input(args.infile)
    bbox.save_rois(rois, args.outfile, args.infile)

if __name__ == '__main__':
    main()

