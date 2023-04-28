import ant_tracking
import numpy as np
import argparse
from matplotlib import pyplot as plt
from os.path import abspath
import collections
#import metadata
#import constants
import cv2
import copy
import sys
import warnings

COLUMN_NAMES = [['filename', 'id', 'x0', 'y0', 't0', 'x1', 'y1', 't1',
                 'number_warning', 'broken_track']]

DIST_THRESH = 100

def track(vidPath, detects_only = False):
    cap = cv2.VideoCapture(vidPath)
                
    detector = ant_tracking.Detectors()

    """Initialize variable used by Tracker class
    Args:
        dist_thresh: distance threshold. When exceeds the threshold,
                        track will be deleted and new track is created
        max_frames_to_skip: maximum allowed frames to be skipped for
                            the track object undetected
        max_trace_lenght: trace path history length
        trackIdCount: identification of each track object
    Return:
        None
    """
    tracker = ant_tracking.Tracker(50, 1000000, 10, 1)

    # Variables initialization
    # This is the colors of the trace pattern displayed in the video
    track_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
                    (0, 255, 255), (255, 0, 255), (255, 127, 255),
                    (127, 0, 255), (127, 0, 127)]

    frame_count = 0

    img_arr = []
    img_arr_detects = []

    size = (0,0)

    # for writing text on video
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = .25
    
    while(True):
        ret, frame = cap.read()
        frame_count += 1

        if ret == True:
            if frame_count == 1:
                height, width, layers = frame.shape
                size = (width,height)
                fps = cap.get(cv2.CAP_PROP_FPS)
            
            # detects the ants and circles them in green
            centers = detector.Detect(frame)
            
            time = round(frame_count/fps)
            minutes = int(time / 60)
            seconds = time % 60
            text = f'{minutes}:{seconds}'

            # labels the top right corner with the current time
            cv2.putText(frame, str(text), (10,10), font, font_scale, (0, 0, 0), 1)
            # creates a video of just circled ants, not tracked ones

            if (len(centers) > 0):

                if detects_only:
                    img_arr_detects.append(frame)
                    continue

                # comment start
                tracker.Update(centers)
                
                for i in range(len(tracker.tracks)):
                    if (len(tracker.tracks[i].trace) > 1):
                        for j in range(len(tracker.tracks[i].trace)-1):
                            # Draw Trace Line
                            x1 = tracker.tracks[i].trace[j][0][0]
                            y1 = tracker.tracks[i].trace[j][1][0]
                            x2 = tracker.tracks[i].trace[j+1][0][0]
                            y2 = tracker.tracks[i].trace[j+1][1][0]
                            ant_id = tracker.tracks[i].track_id

                            color = track_colors[ant_id%(len(track_colors))]

                            cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)),
                                 color, 2)
                            
                            cv2.putText(frame, str(ant_id), (int(x1)+1, int(y1)), font, font_scale, color, 1)
                # comment end

                # Display the resulting tracking frame
                # cv2.imshow('Tracking', frame)
                
                # this appends the frame with the trace paths on it.
            img_arr.append(frame)
                
            # # Display the original frame
            # cv2.imshow('Original', orig_frame)
                            
        else:
            print("Finished processing video, about to replease the capture")
            cap.release()
            print("Capture successfully released")
            if (detects_only):
                return img_arr_detects, size
            return img_arr, size

def color_spaces(imgPath, outPath):
    nemo = cv2.imread(imgPath)
    nemo = cv2.cvtColor(nemo, cv2.COLOR_RGB2HSV)
    cv2.imwrite(outPath, nemo)


def circle_ants(imgPath):
    frame = cv2.imread(imgPath)
    detector = ant_tracking.Detectors()
    centers = detector.Detect(frame)
    cv2.imwrite(imgPath+'_circled.jpg', frame)


def main():
    
    # vidname = str(sys.argv[1])
    # outname = str(sys.argv[2])
    # no_paths = bool(str(sys.argv[3]))

    # color_spaces('ROI_0_frame.jpg', 'ROI_0_frameHSV.jpg')
    
    # circle_ants('ROI_0_frame.jpg')
    
    vidname = "input/7-7-21_21-BA2_2B_ROI_0.mp4"
    outname = "ROI_tracked_gaussian_blur"
    no_paths = False
    # circled_name = circle_ants(vidname)
    # circle_ants(circled_name, True)

    img_arr, size = track(vidname, no_paths)
    print("compiling video")
    out = cv2.VideoWriter('output/'+outname+'.avi',cv2.VideoWriter_fourcc(*'DIVX'), 15, size)
    for i in range(len(img_arr)):
        out.write(img_arr[i])
    print("releasing compiled video")
    out.release()


if __name__== '__main__':
    main()



