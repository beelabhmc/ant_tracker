from __future__ import division
import subprocess
import argparse
from math import sin, cos, ceil

from vid_meta_data import get_video_dimensions

def read_bboxes(filename, videoname):
    """Load filename and returns a list of the bounding boxes for the
    given video.

    Each bounding box is stored as ((upper_left_x, upper_left_y),
    (width, height), angle), where angle is between 0 and π/2 (radians).
    """
    boxes = []
    # file format: fname [ulx;uly;width;height;angle]+
    for line in open(filename):
        line = line.strip().split()
        if videoname not in line[0]:
            continue
        for i in range(1, len(line)):
            box = list(map(float, line[i].split(',')))
            boxes.append(((box[0], box[1]), (box[2], box[3]), box[4]))
    return boxes

def crop_video(video, out_dir, boxes, logfile=None):
    """Crops the given video, according to boxes, and saves the results
    in out_dir.

    boxes should be a list of bounding boxes, in the same format as
    read_bboxes outputs.

    The resulting videos get saved in out_dir and get '-ROI_%d' appended
    to the end, where %d is the number of the ROI in the boxes list.
    """
    command = 'ffmpeg -y -i {0} -vf "rotate=-{1}:ow=ceil(rotw(-{1})/2)*2:' \
              'oh=ceil(roth(-{1})/2)*2, crop={2}:{3}:{4}:{5}" {6}'
    # Format argument order: input video, rotation angle, width, height,
    #     upper-left x after rotation, upper-left y after rotation, output video
    video_name = '.'.join(video.split('/')[-1].split('.')[:-1])
    H, W = get_video_dimensions(video)
    for i in range(len(boxes)):
        (ulx, uly), (width, height), angle = boxes[i]
        x, y = ulx*cos(angle)+uly*sin(angle), (W-ulx)*sin(angle)+uly*cos(angle)
        x, y, = map(round, (x, y))
        width, height = map(lambda x: 2*ceil(x/2), (width, height))
        outvideo = '%s/%s-ROI_%d.mp4' % (out_dir, video_name, i)
        cmd = command.format(video, angle, width, height, x, y, outvideo)
        print('About to run:\n%s' % cmd)
        output = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT).stdout.decode()
        if logfile is not None:
            open(logfile, 'w').write(output)

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('video',
                            type=str,
                            help='The video to be cropped',
                           )
    arg_parser.add_argument('out_dir',
                            type=str,
                            help='The directory in which to save the '
                                 'videos made.',
                           )
    arg_parser.add_argument('boxes',
                            type=str,
                            help='A text file from which to load the '
                                 'boxes to crop.',
                           )
    args = arg_parser.parse_args()
    crop_video(args.video, args.out_dir, read_bboxes(args.boxes, args.video))

if __name__ == '__main__':
    main()

