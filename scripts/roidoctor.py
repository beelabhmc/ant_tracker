#import logging
import argparse
import os

import numpy as np
from matplotlib import pyplot as plt
import cv2
import tempfile # new
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

    all_rois = []

    while True:
        # Let user draw first ROI
        roi1 = RoiPoly(color='r', fig=fig)

        # Show the image with the first ROI
        fig = plt.figure()
        plt.imshow(img, interpolation='nearest', cmap="Greys")
        plt.colorbar()
    #    roi1.display_roi()

    #    roi_coordinates = roi1.get_roi_coordinates() COME BACK
        roi_coordinates = list(zip(roi1.x, roi1.y))
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
        # bbox.save_rois(new_roi, newroifile)
        all_rois.extend(new_roi)

        cont = input("Draw another ROI? (y/n): ").strip().lower()
        if cont != 'y':
            break

    bbox.save_rois(all_rois, newroifile)


def extract_video_frame(video_path, frame_number=0):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if frame_number >= total_frames:
        raise ValueError(f"Requested frame {frame_number} exceeds total frame count ({total_frames})")

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        raise ValueError(f"Could not read frame {frame_number} from video: {video_path}")
    
    temp_img_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    cv2.imwrite(temp_img_path, frame)
    return temp_img_path


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
    arg_parser.add_argument('-v', '--video',
                            action='store_true',
                            help='Treat the input file as a video.')
    arg_parser.add_argument('--frame',
                            type=int,
                            default=0,
                            help='Frame number to extract from video (default: 0).')
    args = arg_parser.parse_args()

    if not os.path.isfile(args.imgfile):
        arg_parser.error(f"'{args.imgfile}' is not a valid file.")
        
    if args.video:
        imgfile = extract_video_frame(args.imgfile, args.frame)
        print(f"Extracted frame {args.frame} from video.")
    else:
        imgfile = args.imgfile

    draw_roi(imgfile, args.newroifile, args.rightHanded)
    
if __name__ == '__main__':
    main()
