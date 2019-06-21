# The length of each segment split, in seconds
SEGMENT_LENGTH = 600

checkpoint split:
    input:
        "input/{video}.mp4"
    output:
        directory("intermediate/split/{video}")
    log:
        "log-{video}.txt"
    shell:
        "python3.7 scripts/split.py -s %s {input} {output} 2>&1 > log-{wildcards.video}.txt || true" % SEGMENT_LENGTH

rule roidetect:
    input:
        "input/{video}.mp4"
    output:
        "intermediate/rois/{video}.txt"
    shell:
        "python3.7 scripts/roidetect.py {input} {output}"

checkpoint croprotate:
    input:
        "intermediate/split/{video}/{split}.mp4",
        "intermediate/rois/{video}.txt"
    output:
        directory("intermediate/crop/{video}/{split}")
    shell:
        "python3.7 scripts/croprotate {input[0]} {output} {input[1]}"

rule track:
    input:
        "intermediate/crop/{video}/{split}/{roi}.mp4"
    output:
        "intermediate/track/{video}/{split}/{roi}.csv"
    shell:
        "python3.7 scripts/track.py {input} {output}"

def aggregate_rois_input(wildcards):
    split_out = checkpoints.split.get(**wildcards).output[0]
    return expand("intermediate/track/{video}/{split}/{roi}.csv",
                  **wildcards,
                  split=glob_wildcards(os.path.join(split_out, '{split}.mp4')).i)

rule aggregate_rois:
    input:
        aggregate_rois_input
    output:
        "intermediate/aggregate/{video}/{roi}.txt"
    shell:
        "python3.7 scripts/combinetrack.py {output} {input}"

