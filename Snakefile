rule split:
    input:
        'input/{video}.mp4'
    output:
        'intermediate/split/{video}-{split}.mp4'
    script:
        'python scripts/split.py -s 600 {input} intermediate/split'

rule crop:
    input:
        'intermediate/split/{video}-{split}.mp4',
        'intermediate/roi_labels.txt'
    output:
        'intermediate/crop/{video}-{split}-ROI_{roi}.mp4'
    script:
        'python scripts/crop.py {input[0]} intermediate/crop {input[1]}'

rule track:
    input:
        'intermediate/crop/{video}-{split}-ROI_{roi}.mp4'
    output:
        'intermediate/track/{video}-{split}-ROI_{roi}.csv'
    script:
        'python scripts/track.py {input} {output}'

