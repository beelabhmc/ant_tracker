#!/usr/bin/python3
import argparse
import shlex
import subprocess
import os, os.path
# os.environ['OPENBLAS_NUM_THREADS'] = '1'  # PLEASE CHANGE ME!


def path_split(path):
    """Takes a path and splits it into a list, where the last item is
    the file name and all items before it are folders on the path.
    """
    path = os.path.splitext(path)[0]
    folders = []
    while 3:
        path, folder = os.path.split(path)
        if folder:
            folders.append(folder)
        else:
            if path:
                folders.append(path)
            return folders[::-1]

def run_pipeline(args, files):
    snakemake = shlex.split('python3.7 -m snakemake')
    process = subprocess.Popen(snakemake+args+files)
    process.wait()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('infiles',
                        nargs='+',
                        type=str,
                        help='A list of files to process.')
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument('-l', '--labels',
                              dest='edges',
                              action='store_const',
                              const=False,
                              default=True,
                              help='Only output the ROI labels, and not '
                                   'the edges.')
    output_group.add_argument('-e', '--edges',
                              dest='labels',
                              action='store_const',
                              const=False,
                              default=True,
                              help='Only output the edge crossings, and not '
                                   'label the ROIs.')
    parser.add_argument('-s', '--snakemake-arguments',
                        dest='args',
                        default='-pk --cores=32',
                        help='Any arguments to pass into snakemake, default = '
                             "'-pk --cores=32'")
    args = parser.parse_args()
    infiles = []
    for infile in map(lambda x: path_split(x)[1:], args.infiles):
        if args.labels:
            infiles.append(os.path.join(*(['output']+infile+['labels.png'])))
        if args.edges:
            infiles.append(os.path.join(*(['output']+infile+['edges.csv'])))
    run_pipeline(shlex.split(args.args), infiles)

if __name__ == '__main__':
    main()

