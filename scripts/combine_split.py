import argparse

def load_file(filename):
    """Returns a list of all ants found in filename, without fName or id."""
    f = open(filename)
    ants = []
    for line in f:
        ants.append(tuple(f.readline().split(',')[2:]))
    return ants

def save_combination(outfile, splits, sep=''):
    """Takes all of the tracks stored in splits and saves them all
    consecutively into one file.
    """
    f = open(outfile, 'w')
    id_num = 0
    f.write('id, X, Y')
    # This does not handle ants who are moving across the video when the
    # split happens
    for split in splits:
        for ant in split:
            f.write('%d,%s\n' % id_num, ','.join(map(str, ant)))
            id_num += 1
        if sep:
            f.write('%s\n' % sep)
            id_num = 0
    f.close()

def combine(filenames, outfile, sep=''):
    """Takes the list of files in filenames and combines them into one
    file, saving the result to outfile.
    """
    save_combination(outfile, map(load_file, filenames), sep)

def main():
    args = argparse.ArgumentParser()
    args.add_argument('destination',
                      type=str,
                      help='The file in which to write all of the tracks.',
                     )
    args.add_argument('source_files',
                      type=str,
                      nargs='+',
                      help='All the files which are to be combined.',
                     )
    args.add_argument('--separator',
                      dest='sep',
                      default=None,
                      type=str,
                      help='A string to place between each file.',
                     )
    args = args.parse_args()
    combine(args.source_files, args.destination, sep=args.sep)

if __name__ == '__main__':
    main()

