#!/usr/local/bin/python3
import subprocess
import shlex
import json

# function to find the resolution of the input video file
def get_video_dimensions(input_video):
    """Returns a tuple with the video dimensions as (height, width)"""
    # run the ffprobe process, decode stdout into utf-8 & convert to JSON
    cmd = "ffprobe -v quiet -print_format json -show_streams".split(' ') \
            + [input_video]
    probe_output = json.loads(subprocess.check_output(cmd).decode('utf-8'))
    # for example, find height and width
    height = probe_output['streams'][0]['height']
    width = probe_output['streams'][0]['width']
    return height, width
    
