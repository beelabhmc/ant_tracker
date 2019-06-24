import glob
import os
import os.path
import argparse

import constants

def rename_all(vid_dir, colony_num, box_region):
    """Takes all videos in the directory vid_dir and renames them to
    the naming scheme:
        C{colony_number}{box_region}-seg{s}.mp4
    where s is the segment number of that video (segments are assumed to
    be alphabetical).
    """
    c=0
    vids = glob.glob(os.path.join(constants.DIRECTORY, vid_dir, '*.mp4'))
    vids.sort()
    
    for vidName in vids:
        command = 'mv {} {}'.format(vidName,
                    os.path.join(constants.DIRECTORY,
                                 'C{}{}-seg{}.mp4'\
                                    .format(constants.DIRECTORY,
                                            colony_num,
                                            box_region,
                                            c
                                           )
                                )
                    )
        c+=1
        os.system(command)


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--v',
                            dest = 'vid_dir',
                            type=str,
                            nargs='+',
                            required=True,
                            help='The directories of the videos, separated '
                                 'by spaces.'
                           )
    arg_parser.add_argument('--c',
                            dest = 'colony_number',
                            type=str,
                            nargs='+',
                            required=True,
                            help='The colony numbers, separated by spaces')
    arg_parser.add_argument('--b',
                            dest = 'box_region',
                            type=str,
                            nargs='+',
                            required=True,
                            help='The box regions (R,D,O), separated by spaces')
    args = arg_parser.parse_args()
    if len(set(map(len,(args.box_region,args.vid_dir,args.colony_number)))) != 1:
        args.error('The given arguments must be the same length.')
    for vid_dir, colony, box in zip(args.vid_dirs,
                                args.colony_numbers, args.box_regions):
        rename_all(vid_dir, colony, box)

if __name__== '__main__':
    main()

