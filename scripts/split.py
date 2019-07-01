import csv
import subprocess
import re
import math
import json
import os
import os.path
import argparse

import constants

re_length = re.compile(r'Duration: (\d{2}):(\d{2}):(\d{2})\.\d+,')

def by_manifest(filename, destination, manifest, vcodec='copy', acodec='copy',
                      extra='', **kwargs):
    """ Split video into segments based on the given manifest file.

    Arguments:
        filename (str)      - Location of the video.
        destination (str)   - Location to place the output videos
                              (doesn't actually work because I don't know how
                               the manifest works --Jarred)
        manifest (str)      - Location of the manifest file.
        vcodec (str)        - Controls the video codec for the ffmpeg video
                              output.
        acodec (str)        - Controls the audio codec for the ffmpeg video
                              output.
        extra (str)         - Extra options for ffmpeg.
    """
    if not os.path.exists(manifest):
        print('File does not exist:', manifest)
        raise SystemExit

    with open(manifest) as manifest_file:
        manifest_type = manifest.split('.')[-1]
        if manifest_type == 'json':
            config = json.load(manifest_file)
        elif manifest_type == 'csv':
            config = csv.DictReader(manifest_file)
        else:
            print('Format not supported. File must be a csv or json file')
            raise SystemExit

        split_cmd = 'ffmpeg -loglevel warning -i \'{}\' -vcodec {} ' \
                    '-acodec {} -y {}'.format(filename, vcodec, acodec, extra)
        split_count = 1
        split_error = []
        try:
            fileext = filename.split('.')[-1]
        except IndexError as e:
            raise IndexError('No . in filename. Error: ' + str(e))
        for video_config in config:
            split_str = ''
            try:
                split_start = video_config['start_time']
                split_length = video_config.get('end_time', None)
                if not split_length:
                    split_length = video_config['length']
                filebase = video_config['rename_to']
                if fileext in filebase:
                    filebase = '.'.join(filebase.split('.')[:-1])

                split_str = ' -ss {} -t {} "{}.{}"' \
                            .format(split_start, split_length, filebase, fileext)
                print('#######################################################')
                print('About to run: '+split_cmd+split_str)
                print('#######################################################')
                output = subprocess.Popen(split_cmd+split_str,
                                          shell = True, stdout =
                                          subprocess.PIPE).stdout.read()
            except KeyError as e:
                print( '############# Incorrect format ##############')
                if manifest_type == 'json':
                    print('The format of each json array should be:')
                    print('{start_time: <int>, length: <int>, rename_to: '
                          '<string>}')
                elif manifest_type == 'csv':
                    print('start_time,length,rename_to should be the first '
                          'line ')
                    print('in the csv file.')
                print('#############################################')
                print(e)
                raise SystemExit



def by_seconds(filename, destination, split_length, vcodec='copy',
               acodec='copy', extra='', **kwargs):
    if not os.path.isdir(destination):
        os.makedirs(destination)
    if split_length <= 0:
        print('Split length must be positive')
        raise SystemExit
    try:
        video_length = metadata.get_video_duration(filename)
    except RuntimeError as re:
        print("Can't determine video length, copying video without splitting")
        destination = os.path.join(destination, '0.mp4')
        subprocess.Popen(f'cp "{filename}" "{destination}"', shell=True)
        return
    split_count = math.ceil(video_length / split_length)
    if(split_count == 1):
        print('Video length is less then the target split length.')
        destination = os.path.join(destination, '0.mp4')
        subprocess.Popen(f'cp "{filename}" "{destination}"', shell=True)
        return

    # we use -y to force overwrites of output files
    split_cmd = f'ffmpeg -loglevel warning -y -i \'filename{}\' -vcodec ' \
                f'{vcodec} -acodec {acodec} {extra}'
    # get the filename without the file ext
    filebase = os.path.basename(filename)
    filebase, fileext = os.path.splitext(filebase)
    for n in range(0, split_count):
        if n == 0:
            split_start = 0
        else:
            split_start = split_length * n
        split_str = f' -ss {split_star} -t {split_length} {destination}{n}.mp4'
        print('About to run:', split_cmd, split_str, sep='')
        output = subprocess.Popen(split_cmd+split_str, shell=True,
                                  stdout=subprocess.PIPE,
                                 ).stdout.read()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename',
                        type=str,
                        help='The name of the file to split',
                       )
    parser.add_argument('destination',
                        type=str,
                        help='The directory in which to save the split videos.',
                       )
    parser.add_argument('-s', '--split-size',
                        dest='split_length',
                        type=int,
                        help='Split or chunk size in seconds, for example 10',
                       )
    parser.add_argument('-m', '--manifest',
                        dest='manifest',
                        type=str,
                        help='Split video based on a json manifest file. ',
                       )
    parser.add_argument('-v', '--vcodec',
                        dest='vcodec',
                        type=str,
                        default='copy',
                        help='Video codec to use. If unspecified, it defaults '
                             'to the one in the source video.',
                       )
    parser.add_argument('-a', '--acodec',
                        dest='acodec',
                        type=str,
                        default='copy',
                        help='Audio codec to use. If unspecified, it defaults '
                             'to the one in the source video',
                       )
    parser.add_argument('-e', '--extra',
                        dest='extra',
                        type=str,
                        default='',
                        help='Extra options for ffmpeg, e.g. "-e -threads 8". ',
                       )
    args = parser.parse_args()
    if args.destination[-1] != '/':
        args.destination += '/'

    if args.filename and args.manifest:
        by_manifest(**(args.__dict__))
    elif args.filename and args.split_length:
        by_seconds(**(args.__dict__))
    else:
        parser.print_help()
        raise SystemExit

if __name__ == '__main__':
    main()

