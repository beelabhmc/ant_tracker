from __future__ import division
import subprocess
import argparse
from math import sin, cos, ceil
import os
import os.path

import metadata
import bbox

def crop_video(video, out_dir, boxes, logfile=None):
    """Crops the given video, according to boxes, and saves the results
    in out_dir.

    boxes should be a list of bounding boxes, in the same format as
    read_bboxes outputs.

    The resulting videos get saved in out_dir and get '-ROI_%d' appended
    to the end, where %d is the number of the ROI in the boxes list.
    """
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    command = 'ffmpeg -y -i {0} -strict -2 -vf "rotate=-{1}:' \
              'ow=ceil(rotw(-{1})/2)*2:oh=ceil(roth(-{1})/2)*2, ' \
              'crop={2}:{3}:{4}:{5}" {6}'
              # The -strict -2 is here because ffmpeg sometimes insists on
              # using experimental codices. I don't know why it does that,
              # but this allows it to continue.
    # Format argument order: input video, rotation angle, width, height,
    #     upper-left x after rotation, upper-left y after rotation, output video
    video_name = os.path.splitext(os.path.basename(video))[0]
    H, W = metadata.get_video_dimensions(video)
    for i in range(len(boxes)):
        (ulx, uly), (width, height), angle, *_ = boxes[i]
        x, y = ulx*cos(angle)+uly*sin(angle), (W-ulx)*sin(angle)+uly*cos(angle)
        x, y, = map(round, (x, y))
        width, height = map(lambda x: 2*ceil(x/2), (width, height))
        outvideo = '%s/ROI_%d.mp4' % (out_dir, i)
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
    crop_video(args.video, args.out_dir, bbox.read_bboxes(args.boxes))

if __name__ == '__main__':
    main()

