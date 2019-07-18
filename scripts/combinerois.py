import argparse
import os, os.path
import re

def combine_rois(rois, outfile):
    if not os.path.isdir(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))
    outfile = open(outfile, 'w')
    for f in rois:
        name = os.path.splitext(os.path.basename(f))[0]
        for line in open(f):
            line = re.sub(r'[^,]+,', f'{name},', line, count=1)
            outfile.write(line)
    outfile.close()

def main():
    args = argparse.ArgumentParser()
    args.add_argument('outfile',
                      type=str,
                      help='The file to which to write the combined results to.')
    args.add_argument('infiles',
                      nargs='+',
                      type=str,
                      help='The files to combine, separated by spaces.')
    args = args.parse_args()
    combine_rois(args.infiles, args.outfile)

if __name__ == '__main__':
    main()


