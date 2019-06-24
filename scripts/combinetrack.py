import argparse

def combine_split_track(tracks, outfile, filesep='SPLIT #{number}:\n'):
    """Combines a list of tracks (specified via filenames) into one
    file, at the location specified by outfile.

    filesep is used as a delimiter to separate the different files.
    Valid format arguments to be used in it are:
      · number - The number corresponding to this split
    """
    f = open(outfile, 'w')
    for infile in tracks:
        f.write(filesep.format(number=infile.split('/')[-2]))
        f.write(open(infile).read().strip()+'\n')
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
    args.add_argument('--filesep',
                      type=str,
                      dest='filesep',
                      default='SPLIT #{number}:\n',
                      help='A string to preface each file being merged.',
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
    combine_split_track(args.infiles, args.outfile, filesep=args.filesep)

if __name__ == '__main__':
    main()

