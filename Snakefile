configfile: 'config.yaml'

rule convert_h264_to_mp4:
    input:
        '{video}.h264'
    output:
        '{video}.mp4'
    shell:
        'ffmpeg -framerate %d -i {input} -c copy {output}' \
            % config['h264-framerate']

checkpoint split:
    input:
        'input/{video}.mp4'
    output:
        directory('intermediate/split/{video}')
    priority: 20
    shell:
        'python3.7 scripts/split.py -s %s {input} {output}' \
            % config['segment-length']

rule roidetect:
    input:
        'input/{video}.mp4'
    output:
        'intermediate/rois/{video}.txt'
    shell:
        'python3.7 scripts/roidetect.py {{input}} {{output}} -u {} -s {} -v {} '
        '-o {} -d {} -c {} -e {} -p {}' \
        .format(*(config['roi-detection'][x]
                  for x in ['hsv-hue-tolerance', 'hsv-sat-minimum',
                            'hsv-value-minimum', 'smooth-open-size',
                            'smooth-dilate-size', 'smooth-close-size',
                            'polygon-epsilon', 'roi-bbox-padding']))

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
    priority: 10
    threads: config['croprot']['cores']
    shell:
        'python3.7 scripts/croprotate.py -c %d {input[0]} {output} {input[1]}' \
            % config['croprot']['cores']

def track_input(wildcards):
    checkpoints.croprotate.get(**wildcards).output[0]
    return 'intermediate/crop/{video}/{split}/ROI_{roi}.mp4'

rule track:
    input:
        track_input
    output:
        'intermediate/track/{video}/{split}/ROI_{roi}.csv'
    shell:
        'python3.7 scripts/track.py {{input}} {{output}} -m {} -c {} -g {} -tf '
        '{} -b {} -n {} -it {} -ot {} -vt {} -ki {} -ko {} -km {} -v {}' \
        .format(*(config['tracks'][x]
                  for x in ['min-blob', 'count-warning-threshold',
                            'num-gaussians', 'num-training-frames',
                            'minimum-background-ratio', 'cost-of-nonassignment',
                            'invisible-threshold', 'old-age-threshold',
                            'visibility-threshold', 'kalman-initial-error',
                            'kalman-motion-noise', 'kalman-measurement-noise',
                            'min-visible-count']))

def aggregate_splits_input(wildcards):
    split_out = checkpoints.split.get(video=wildcards.video).output[0]
    track_out = 'intermediate/track/{video}/{split}/ROI_{roi}.csv'
    return expand(track_out, **wildcards,
                  split=glob_wildcards(os.path.join(split_out, '{i}.mp4')).i)

rule aggregate_splits:
    input:
        aggregate_splits_input
    output:
        'intermediate/aggregate/{video}/ROI_{roi}.csv'
    shell:
        'python3.7 scripts/combinetrack.py {output} {input}'

def aggregate_rois_input(wildcards):
    crop_out = checkpoints.croprotate.get(**wildcards, split=0).output[0]
    aggregate_split_out = 'intermediate/aggregate/{video}/ROI_{roi}.csv'
    crop_out = os.path.join(crop_out, 'ROI_{i}.mp4')
    rois = glob_wildcards(crop_out).i
    # print(crop_out, rois, sep='\n')
    return expand(aggregate_split_out, **wildcards, roi=rois)

rule aggregate_rois:
    input:
        aggregate_rois_input
    output:
        'output/{video}/tracks.csv'
    shell:
        'python3.7 scripts/combinerois.py {output} {input}'

rule sort_aggregated_rois:
    input:
        'output/{video}/tracks.csv'
    output:
        'output/{video}/sorted.csv'
    shell:
        'cat {input} | sort --field-separator=, -nk 5'
        ' > {output}'
 
rule edge_from_tracks:
    input:
        'output/{video}/sorted.csv',
        'intermediate/rois/{video}.txt'
    output:
        'output/{video}/edges.csv'
    shell:
        'python3.7 scripts/edgefromtrack.py {input[0]} {output} {input[1]}'

rule roi_label:
    input:
        'input/{video}.mp4',
        'intermediate/rois/{video}.txt'
    output:
        'output/{video}/labels.png'
    shell:
        'python3.7 scripts/roilabel.py {input[0]} {input[1]} {output}'

