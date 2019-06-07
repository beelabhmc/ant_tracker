from __future__ import division
import os
import argparse

def read_bbox(boxfile, video):
    """Read the ROI labels from the given file into a dictionary mapping
    names of the boxes to the coordinates and dimensions, for the video
    given.
    """
    bboxes = {}
    for line in open(boxfile):
        line = line.strip().split('\t')
        if video in line[0]:
            boxes = line[1:]
            for i in range(len(boxes)):
                bboxes['ROI_%d' % i] = map(int, boxes[i].split(','))
    from pprint import pprint
    pprint(bboxes)
    return bboxes

def crop_video(video, out_dir, boxes, logfile='/dev/null'):
    """Crops the given video, according to boxes, and saves the results
    in out_dir.

    Boxes should be either a string, in which case it is a path to the
    file from which to read the boxes, or a dict, in which case it is
    the boxes.

    The dict should have keys consisting of the name of the ROI and
    values consisting of a list of coords of the box, formatted as
    [x_upper_left_corner, y_upper_left_corner, x_width, y_width]

    If logfile is given, then the logs of ffmpeg gets stored in that
    file. Otherwise, the logs from ffmpeg are ignored.
    """
    if out_dir[-1] != '/':
        out_dir += '/'
    video_name = '.'.join(video.split('/')[-1].split('.')[:-1])
    par_name = '-'.join(video_name.split('-')[:-1]) # BBox was made for parent
    if type(boxes) is str:
        boxes = read_bbox(boxes, par_name)
    for box in boxes.keys():
        x, y, w, h = boxes[box]
        rect = '%d:%d:%d:%d' % (w, h, x, y)
        crop_name = '%s%s-%s.mp4' % (out_dir, video_name, box)
        command = 'ffmpeg -y -i %s -vf crop=%s %s >> %s' \
                  % (video, rect, crop_name, logfile)
        os.system(command)
    return boxes

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
    crop_video(args.video, args.out_dir, args.boxes)

if __name__ == '__main__':
    main()

