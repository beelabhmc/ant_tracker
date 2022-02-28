import subprocess
import argparse
from math import sin, cos, ceil
import os
import os.path
from concurrent.futures import ProcessPoolExecutor

import metadata
import bbox

def run_cmd(cmd):
    """Execute the command. A basic helper function for the next line."""
    print(f'About to run:\n{cmd}')
    output = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT).stdout.decode()
    return output 

def crop_video(Dict, video, out_dir, boxes, cores=1, logfile=None):
    """Crops the given video, according to boxes, and saves the results
    in out_dir.

    boxes should be a list of bounding boxes, in the same format as
    read_bboxes outputs.

    The resulting videos get saved in out_dir and get '-ROI_%d' appended
    to the end, where %d is the number of the ROI in the boxes list.

    Cores is an optional argument. If specified, it will run this many
    ffmpeg operations in parallel, increasing execution speed. If cores
    is 0, then it will run all operations in parallel.
    """
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    command = 'ffmpeg -y -i {0} -strict -2 -vf "rotate={1}:' \
              'ow=ceil(rotw({1})/2)*2:oh=ceil(roth({1})/2)*2, ' \
              'crop={2}:{3}:{4}:{5}" {6}'
              # The -strict -2 is here because ffmpeg sometimes insists on
              # using experimental codices. I don't know why it does that,
              # but this allows it to continue.

              # Rotates positive because ffmpeg rotate clockwise and our angle is measured positively
              # counterclockwise 
    # Format argument order: input video, rotation angle, width, height,
    #     upper-left x after rotation, upper-left y after rotation, output video
    video_name = os.path.splitext(os.path.basename(video))[0]
    H, W = metadata.get_video_dimensions(video)
    cmds = []
    for i in range(len(boxes)):
        (ulx, uly), (width, height), angle = boxes[i].box
        #Changed to new formula 
        new_ulx = ulx*cos(angle) - uly*sin(angle) + H*sin(angle)
        new_uly = ulx*sin(angle)+uly*cos(angle)
        new_ulx, new_uly, = map(round, (new_ulx, new_uly))
        width, height = map(lambda x: 2*ceil(x/2), (width, height))
        outvideo = f'{out_dir}/ROI_{Dict[i]}.mp4'
        cmds.append(command.format(video, angle, width, height, new_ulx, new_uly, outvideo))
    if cores == 0:
        cores = len(cmds)
    outputs = list(ProcessPoolExecutor(max_workers=cores).map(run_cmd, cmds))
    if logfile is not None:
        open(logfile, 'a').write('\n\n'.join(outputs))

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('video',
                            type=str,
                            help='The video to be cropped')
    arg_parser.add_argument('out_dir',
                            type=str,
                            help='The directory in which to save the '
                                 'videos made.')
    arg_parser.add_argument('boxes',
                            type=str,
                            help='A text file from which to load the '
                                 'boxes to crop.')
    arg_parser.add_argument('-c', '--cores',
                            type=int,
                            default=1,
                            dest='cores',
                            help='The number of cores to use during splitting, '
                                 'default 1. If multiple cores are specified, '
                                 'then multiple crops will be done in '
                                 'parallel.')
    Dict = {0:42, 1:122, 2:121, 3:41, 4:12, 5:40, 6:112, 7:8, 8:11, 9:6, 10:10, 11:4, 12:111, 13:2, 14:60, 15:0, 16:1, 17:3, 18:20, 19:7, 20:5, 21:211, 22:31, 23:21, 24:22, 25:30, 26:50, 27:212, 28:222, 29:221, 30:32}
    args = arg_parser.parse_args()
    crop_video(Dict, args.video, args.out_dir, bbox.read_bboxes(args.boxes),
               cores=args.cores)

if __name__ == '__main__':
    main()

