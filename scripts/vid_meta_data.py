import subprocess
import re

regex_height = re.compile(r'^height=([0-9]+)$', re.MULTILINE)
regex_width = re.compile(r'^width=([0-9]+)$', re.MULTILINE)

# function to find the resolution of the input video file
def get_video_dimensions(input_video):
    """Takes a path to a video file and returns a tuple containing the
    video's height and width in that order.
    """
    cmd = 'ffprobe -v quiet -show_streams {}' .format(input_video).split()
    output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)\
                .stdout.decode()
    height = int(re.search(regex_height, output).group(1))
    width = int(re.search(regex_width, output).group(1))
    return height, width
    
