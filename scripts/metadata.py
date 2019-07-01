import subprocess
import re

height_regex = re.compile(r'^height=([0-9]+)$', re.MULTILINE)
width_regex = re.compile(r'^width=([0-9]+)$', re.MULTILINE)
duration_regex = re.compile(r'^duration=([0-9]+[.][0-9]+)$', re.MULTILINE)
frames_regex = re.compile(r'^nb_frames=([0-9]+)$', re.MULTILINE)
fps_regex = re.compile(r'^avg_frame_rate=([0-9]+/[0-9]+)$', re.MULTILINE)

def get_video_dimensions(input_video):
    """Takes a path to a video file and returns a tuple containing the
    video's height and width in that order.
    """
    cmd = f'ffprobe -show_streams {input_video}'.split()
    output = subprocess.run(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT).stdout.decode()
    try:
        height = int(re.search(height_regex, output).group(1))
        width = int(re.search(width_regex, output).group(1))
    except AttributeError as e:
        raise RuntimeError('Unparsable ffprobe output:\n%s\n\nfrom command:\n%s'
                            % (output, ' '.join(cmd))) from e
    return height, width

def get_video_duration(input_video):
    """Returns the duration of the given video."""
    cmd = f'ffprobe -show_streams {input_video}'.split()
    output = subprocess.run(cmd, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT).stdout.decode()
    try:
        return float(re.search(duration_regex, output).group(1))
    except AttributeError as e:
        raise RuntimeError('Unparsable ffprobe output:\n{}\nfrom command:\n{}'\
                           .format(output, ' '.join(cmd))) from e
    
def get_video_frames(input_video):
    """Returns the number of frames in the given video."""
    cmd = f'ffprobe -show_streams {input_video}'.split()
    output = subprocess.run(cmd, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT).stdout.decode()
    try:
        return int(re.search(frames_regex, output).group(1))
    except AttributeError as e:
        raise RuntimeError('Unparsable ffprobe output:\n{}\nfrom command:\n{}'\
                           .format(output, ' '.join(cmd))) from e

def get_video_fps(input_video):
    """Returns the average framerate in the given video."""
    cmd = f'ffprobe -show_streams {input_video}'.split()
    output = subprocess.run(cmd, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT).stdout.decode()
    try:
        return eval(re.search(fps_regex, output).group(1))
    except AttributeError as e:
        raise RuntimeError('Unparsable ffprobe output:\n{}\nfrom command:\n{}'\
                           .format(output, ' '.join(cmd))) from e

