# The length of the segments to split, in seconds
SEGMENT_LENGTH = 600

checkpoint split:
    input:
        'input/{video}.mp4'
    output:
        directory('intermediate/split/{video}')
    shell:
        'python3.7 scripts/split.py -s %s {input} {output}' % SEGMENT_LENGTH

rule roidetect:
    input:
        'input/{video}.mp4'
    output:
        'intermediate/rois/{video}.txt'
    shell:
        'python3.7 scripts/roidetect.py {input} {output}'

def croprotate_input(wildcards):
    indir = checkpoints.split.get(video=wildcards.video).output[0]
    return [os.path.join(indir, '{split}.mp4').format(split=wildcards.split),
            'intermediate/rois/{video}.txt'.format(video=wildcards.video),
           ]

checkpoint croprotate:
    input:
        croprotate_input
    output:
        directory('intermediate/crop/{video}/{split}')
    shell:
        'python3.7 scripts/croprotate.py {input[0]} {output} {input[1]}'

def track_input(wildcards):
    checkpoints.croprotate.get(**wildcards).output[0]
    return 'intermediate/crop/{video}/{split}/ROI_{roi}.mp4'

rule track:
    input:
        track_input
    output:
        'intermediate/track/{video}/{split}/ROI_{roi}.csv'
    shell:
        'python3.7 scripts/track.py {input} {output}'

def aggregate_rois_input(wildcards):
    split_out = checkpoints.split.get(video=wildcards.video).output[0]
    track_out = 'intermediate/track/{video}/{split}/ROI_{roi}.csv'
    return expand(track_out, **wildcards,
                  split=glob_wildcards(os.path.join(split_out, '{i}.mp4')).i)

rule aggregate_rois:
    input:
        aggregate_rois_input
    output:
        'intermediate/aggregate/{video}/ROI_{roi}.txt'
    shell:
        'python3.7 scripts/combinetrack.py {output} {input}'
 
