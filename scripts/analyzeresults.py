import os, os.path
import argparse
from collections import defaultdict



def walking_table(edges_file, outfile):
    if not os.path.isdir(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))
    
    counts = defaultdict(int)

    with open(edges_file) as inp:
        header = inp.readline()

        for line in inp:
            parts = line.strip().split(',')

            roi = parts[0]
            edge0 = parts[2]
            edge1 = parts[6]

            key = (roi, edge0, edge1)
            counts[key] += 1

    with open(outfile, 'w') as outp:
        outp.write('roi,edge0,edge1,count\n')

        for (roi, edge0, edge1), count in counts.items():
            outp.write(f'{roi},{edge0},{edge1},{count}\n')



def sum_merge(merge_folder, outfile):
    if not os.path.isdir(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))

    roi_counts = defaultdict(int)

    # loop over splits in merge
    for split in os.listdir(merge_folder):
        split_path = os.path.join(merge_folder, split)

        if not os.path.isdir(split_path):
            continue

        # loop over ROI folders
        for roi in os.listdir(split_path):
            roi_path = os.path.join(split_path, roi)

            if not os.path.isdir(roi_path):
                continue

            # count video files in this ROI folder
            count = sum(
                1 for f in os.listdir(roi_path)
                if f.endswith('.mp4')
            )

            # accumulate across splits
            roi_counts[roi] += count

    # write output
    with open(outfile, 'w') as outp:
        outp.write('roi,total_merge_count\n')

        for roi, count in roi_counts.items():
            outp.write(f'{roi},{count}\n')


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('infile',
                            type=str,
                            help='The file to read edges data in from.')
    arg_parser.add_argument('outfile',
                            type=str,
                            help='The file to write the counted edges data.')
    arg_parser.add_argument('infile2',
                            type=str,
                            help='The file containing intermediate merge files')
    arg_parser.add_argument('outfile2',
                            type=str,
                            help='The file to write the counted merge data')
    args = arg_parser.parse_args()


    walking_table(args.infile, args.outfile)
    sum_merge(args.infile2, args.outfile2)

if __name__ == '__main__':
    main()
