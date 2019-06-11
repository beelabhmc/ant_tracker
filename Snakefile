NUM_SEGMENTS_PER_VIDEO = 6
NUM_ROIS = 3

rule split:
    input:
        'input/{video}.mp4'
    output:
        expand('intermediate/split/{{video}}-{split}.mp4',
               split=range(NUM_SEGMENTS_PER_VIDEO))
    shell:
        'python3.7 scripts/split.py -s 600 {input} intermediate/split'

rule crop:
    input:
        'intermediate/split/{video}-{split}.mp4',
        'intermediate/roi_labels.txt'
    output:
        expand('intermediate/crop/{{video}}-{{split}}-ROI_{roi}.mp4',
               roi=range(NUM_ROIS))
    shell:
        'python3.7 scripts/crop.py {input[0]} intermediate/crop {input[1]}'

rule track:
    input:
        'intermediate/crop/{video}-{split}-ROI_{roi}.mp4'
    output:
        'intermediate/track/{video}-{split}-ROI_{roi}.csv'
    shell:
        'python3.7 scripts/track.py {input} {output}'

