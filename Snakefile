configfile: 'config.yaml'
from ast import literal_eval

# so that we can queue videos by listing them in config file
videos = config["videos"]

rule all:
    input:
        expand("output/{video}/edges.csv", video=videos),
        expand("output/{video}/sorted.csv", video=videos),
        expand("output/{video}/tracks.csv", video=videos)




# The pipeline only works with mp4 files. If the input is a mov file, it converts it to mp4 and 
# puts the new mp4 file into the input directory.
#rule convert_mov_to_mp4:
 #   input:
  #      'input/{video}.mov'
   # output:
    #    'input/{video}.mp4'
   # shell:
    #    'ffmpeg -i {input} -vcodec h264 -acodec mp2 {output}'


# Video shakes at the beginning and end, so we trim the first and last 5 seconds to ensure consistency.
# Please note that I am not 100 percent sure this works as intended, but it doesn't crash the program.
rule trim:
    input:
        'input/{video}.mp4'
    output:
        'intermediate/trim/{video}.mp4'
    shell:
        '''
        duration=$(ffprobe -v error -show_entries format=duration -of csv=p=0 {input}); \
        duration=$(bc <<< "$duration - 5"); \
        echo $duration; \
        ffmpeg -ss 00:00:05 -to $duration -i {input} -c copy {output}
        '''


# Detects the regions of interest using the first frame of the input video. Please ensure all ArUco
# tags are clearly visible. Change the year the video was recorded in the config file, as the layout
# of the videos produced in 2021 is different than 2023. Currently, the program attempts to continue
# even if six (rather than seven) tags are detected.
rule roidetect:
    input:
        'intermediate/trim/{video}.mp4'
    output:
        'intermediate/rois/{video}.txt'
    shell:
        'python scripts/roidetect.py {input} {output} -y ' + str(config["roidetect"]["year"])


# Splits videos that are too long into 10 minute chunks. Note that the amount split can be changed
# but the default is 10 minutes. 
checkpoint split:
    input:
        'intermediate/trim/{video}.mp4'
    output:
        directory('intermediate/split/{video}')
    priority: 20
    shell:
        'python scripts/split.py -s %s -l %s {input} {output}' \
            % (config['split']['segment-length'],
               config['split']['min-segment-length'])


def croprotate_input(wildcards):
    indir = checkpoints.split.get(video=wildcards.video).output[0]
    return [os.path.join(indir, '{split}.mp4').format(split=wildcards.split),
            'intermediate/rois/{video}.txt'.format(video=wildcards.video),
           ]


# Crops the input video and creates individual ROI videos. Please check labels.png in the output
# directory. Every black rectangular box is where the crops will occur. 
# WARNING: There is a tendency for cropping to not work properly. Change to the crop directory
# in the intermediate directory and do the command "ls -l *". This should output the size in bytes
# of the file. If the size of the video file is zero, it means 
checkpoint croprotate:
    input:
        croprotate_input
    output:
        directory('intermediate/crop/{video}/{split}')
    priority: 20
    threads: config['croprot']['cores']
    shell:
        'python scripts/croprotate.py -c %d {input[0]} {output} {input[1]}' \
            % config['croprot']['cores']


def track_input(wildcards):
    checkpoints.croprotate.get(**wildcards).output[0]
    return 'intermediate/crop/{video}/{split}/ROI_{roi}.mp4'


# Tracks the ants in each cropped video. The first output (csv) contains all the detected "ants".
# All detected tracks will be in the csv file, regardless if they are an ant or not. The second
# output (mp4) will contain the full video with annotations. Annotations include the ID number 
# assigned to each ant as well as the timestamp. 

# PLEASE CHECK TRACK.PY TO SEE THIRD AND FOURTH OUTPUTS: The third output (mp4) will contain the
# moments a merger was detected. The fourth output (mp4) is the same as the third output, but 
# with annotations.

# The reason why the third and fourth outputs are not under the outputs section in the snakefile
# is because the third and fourth outputs are occasional (it depends on merged ants being detected)
# but output one and two will always occur

# If you would like to read documentation, please go to this website:
# https://docs.google.com/document/d/1htbx2V9Csv76w_K1VIHraufgfp67IIGRi2dBFt5XDXk/edit
rule track:
    input:
        track_input
    threads: 32
    output:
        'intermediate/track/{video}/{split}/ROI_{roi}.csv',
        'intermediate/full_annotation/{video}/{split}/ROI_{roi}.mp4'
    shell:
        'python scripts/track.py {{input}} {{output[0]}} {{output[1]}} -m {} -c {} -g {} -it {} -d {} '
        '-cto {} -ctt {} -cas {} -tt {} -dm {} -tdt {} -ttl {} -nac {} -eb {} -md {}' \
        .format(*(config['tracks'][x]
                  for x in ['min-blob', 'count-warning-threshold',
                            'num-gaussians', 'invisible-threshold', 'min-duration',
                            'canny-threshold-one', 'canny-threshold-two', 
                            'canny-aperture-size', 'thresholding-threshold',
                            'dilating-matrix', 'tracker-distance-threshold',
                            'tracker-trace-length', 'no-ant-counter-frames-total',
                            'edge-border', 'merge-distance']))


def aggregate_splits_input(wildcards):
    split_out = checkpoints.split.get(video=wildcards.video).output[0]
    track_out = 'intermediate/track/{video}/{split}/ROI_{roi}.csv'
    return expand(track_out, **wildcards,
                  split=glob_wildcards(os.path.join(split_out, '{i}.mp4')).i)


# Combines the different tracks.csv files due to the split rule. Also deals with mergers
# and unmergers, and then gets rid of rows in the csv that are not actual ants. This step
# also flags the warning "count-warning-threshold" when necessary. 
rule aggregate_splits:
    input:
        aggregate_splits_input
    output:
        'intermediate/aggregate/{video}/ROI_{roi}.csv'
    shell:
        'python scripts/combinetrack.py {{output}} {{input}} -c {} -d {}' \
        .format(*(config['tracks'][x]
                  for x in ['count-warning-threshold', 'min-duration']))


def aggregate_rois_input(wildcards):
    crop_out = checkpoints.croprotate.get(**wildcards, split=0).output[0]
    aggregate_split_out = 'intermediate/aggregate/{video}/ROI_{roi}.csv'
    crop_out = os.path.join(crop_out, 'ROI_{i}.mp4')
    rois = glob_wildcards(crop_out).i
    print(crop_out, rois, sep='\n')
    return expand(aggregate_split_out, **wildcards, roi=rois)


# combines the aggregate.csv files into one
rule aggregate_rois:
    input:
        aggregate_rois_input
    output:
        'output/{video}/tracks.csv'
    shell:
        'python scripts/combinerois.py {output} {input}'


# this sorts the tracks.csv file by t0 (time ants were first discovered). This file
# is good for comparing human collected data. Note that t0 is the 5th column, hence
# the command "-nk 5"
rule sort_aggregated_rois:
    input:
        'output/{video}/tracks.csv'
    output:
        'output/{video}/sorted.csv'
    shell:
        'cat {input} | sort --field-separator=, -nk 5'
        ' > {output}'


# Loads infile and converts it to which edges were crossed, as defined by the bboxes 
# parameter, and then saves it to outfile.
rule edge_from_tracks:
    input:
        'output/{video}/sorted.csv',
        'intermediate/rois/{video}.txt'
    output:
        'output/{video}/edges.csv'
    shell:
        'python scripts/edgefromtrack.py {input[0]} {output} {input[1]}'


# draws the regions of interest onto a frame of the video. 
rule roi_label:
    input:
        'intermediate/trim/{video}.mp4',
        'intermediate/rois/{video}.txt'
    output:
        'output/{video}/labels.png'
    shell:
        'python scripts/roilabel.py {input[0]} {input[1]} {output} -y ' + str(config["roidetect"]["year"])
        + (' -i' if config['label']['insignificant-vertices'] else '')
