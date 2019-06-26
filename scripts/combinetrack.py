import argparse
import os, os.path

def combine_split_track(tracks, outfile, split_length=600):
    """Combines a list of tracks (specified via filenames) into one
    file, at the location specified by outfile.
    """
    if not os.path.isdir(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))
    f = open(outfile, 'w')
    for i in range(len(tracks)):
        infile = tracks[i]
        for line in open(infile):
            line = line.split(',')
            if line[4] == 't0':
                continue
            line[4] = str(round(split_length*i + float(line[4]), 2))
            line[7] = str(round(split_length*i + float(line[7]), 2))
            line = ','.join(line)
            f.write(line)
    f.close()

def main():
    args = argparse.ArgumentParser()
    args.add_argument('outfile',
                      type=str,
                      help='The file to which to write the combined output.',
                     )
    args.add_argument('infiles',
                      type=str,
                      nargs='+',
                      help='A list of all the files which are to be combined.',
                     )
    args.add_argument('--sort',
                      type=bool,
                      dest='sort',
                      default=True,
                      help='Whether or not to sort the input files. Defaults '
                           'to true. If False, files are unsorted, otherwise, '
                           'files get sorted in alphabetical order.'
                     )
    args = args.parse_args()
    if args.sort:
        args.infiles.sort()
    combine_split_track(args.infiles, args.outfile)

if __name__ == '__main__':
    main()

