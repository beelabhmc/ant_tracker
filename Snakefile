configfile: 'config.yaml'

rule convert_mov_to_mp4:
    input:
        'input/{video}.mov'
    output:
        'input/{video}.mp4'
    shell:
        'ffmpeg -i {input} -vcodec h264 -acodec mp2 {output}'


# Video shakes at the beginning and end, so we trim the first and last 5 seconds to ensure consistency
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

rule roidetect:
    input:
        'intermediate/trim/{video}.mp4'
    output:
        'intermediate/rois/{video}.txt'
    shell:
        'python scripts/roidetect.py {input} {output} -y ' + str(config["roidetect"]["year"])

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

rule track:
    input:
        track_input
    output:
        'intermediate/track/{video}/{split}/ROI_{roi}.csv'
    threads: 32
    shell:
        'python scripts/track.py {{input}} {{output}} -m {} -c {} -g {} -it {} -d {} '
        '-cto {} -ctt {} -cas {} -tt {} -dm {} -tdt {} -ttl {} -nac {} -eb {}' \
        .format(*(config['tracks'][x]
                  for x in ['min-blob', 'count-warning-threshold',
                            'num-gaussians', 'invisible-threshold', 'min-duration',
                            'canny-threshold-one', 'canny-threshold-two', 
                            'canny-aperture-size', 'thresholding-threshold',
                            'dilating-matrix', 'tracker-distance-threshold',
                            'tracker-trace-length', 'no-ant-counter-frames-total',
                            'edge-border']))


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
        'python scripts/combinetrack.py {output} {input}'

def aggregate_rois_input(wildcards):
    crop_out = checkpoints.croprotate.get(**wildcards, split=0).output[0]
    aggregate_split_out = 'intermediate/aggregate/{video}/ROI_{roi}.csv'
    crop_out = os.path.join(crop_out, 'ROI_{i}.mp4')
    rois = glob_wildcards(crop_out).i
    print(crop_out, rois, sep='\n')
    return expand(aggregate_split_out, **wildcards, roi=rois)

rule aggregate_rois:
    input:
        aggregate_rois_input
    output:
        'output/{video}/tracks.csv'
    shell:
        'python scripts/combinerois.py {output} {input}'

rule sort_aggregated_rois:
    input:
        'output/{video}/tracks.csv'
    output:
        'output/{video}/sorted.csv'
    shell:
        'cat {input} | sort --field-separator=, -nk 6'
        ' > {output}'

rule edge_from_tracks:
    input:
        'output/{video}/sorted.csv',
        'intermediate/rois/{video}.txt'
    output:
        'output/{video}/edges.csv'
    shell:
        'python scripts/edgefromtrack.py {input[0]} {output} {input[1]}'


rule roi_label:
    input:
        'intermediate/trim/{video}.mp4',
        'intermediate/rois/{video}.txt'
    output:
        'output/{video}/labels.png'
    shell:
        'python scripts/roilabel.py {input[0]} {input[1]} {output} -y ' + str(config["roidetect"]["year"])
        + (' -i' if config['label']['insignificant-vertices'] else '')
