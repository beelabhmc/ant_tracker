import argparse
import os, os.path
import collections
import constants

def combine_split_track(tracks, outfile, min_duration, count_warning_threshold, split_length=600):
    """Combines a list of tracks (specified via filenames) into one
    file, at the location specified by outfile.
    """

    # filename,id,x0,y0,t0,x1,y1,t1,begin_middle,end_middle,merge_id,
    # 0        1  2  3  4  5  6  7  8            9          10
    # merge_time,unmerge_id,unmerge_time,number_warning,broken_track
    # 11         12         13           14             15

    if not os.path.isdir(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))

    f = open(outfile, 'w')
    times = collections.deque()
    for i in range(len(tracks)):
        infile = tracks[i]
        for line in open(infile):
            line = line.split(',')

            # we skip the headers
            if line[4] == 't0':
                continue

            # line[7] is t1; line[4] is t0
            # deletes track if ant appeared for less than min_duration
            if float(line[7]) - float(line[4]) < min_duration:  # change to min_duration
                print("Skipping line", i, "because it is too short")
                continue

            # line[8] is begin_middle; line[9] is end_middle
            # deletes track if ant appeared and disappeared in middle of track
            if line[8] == "1" and line[9] == "1":
                print("Skipping line", i, "because it started and ended in middle")
                continue

            # line[15] is broken_track
            # deletes track if it is broken
            if line[15] == "1":
                print("Skipping line", i, "because it has a broken track")
                continue

            # this determines number_warning
            t1 = line[7]
            times.append((float(t1), i))
            while times[0][0] <= float(t1) - 5:
                times.popleft()
            if len(times) >= count_warning_threshold:
                print('Warning: detected an unexpected number of tracks at '
                    f't={t1} in {line[0]}')
                for _ in times:
                    line[14] = '1'  # set number warning to 1

            t0 = round(split_length*i + float(line[4]), 2)
            t1 = round(split_length*i + float(line[7]), 2)
            line[4] = "{minute0}.{second0:02d}".format(minute0 = int(t0//60), second0 = int(t0%60))
            line[7] = "{minute1}.{second1:02d}".format(minute1 = int(t1//60), second1 = int(t1%60))

            line = line[:8] + line[14:]      
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
    args.add_argument('-d', '--min-duration',
                            dest='min_duration',
                            type=float,
                            default=constants.MIN_DURATION,
                            help='The minimum duration (in seconds) for which '
                                 'a track must be present to be recorded '
                     )
    args.add_argument('-c', '--count-threshold',
                            dest='count_threshold',
                            type=int,
                            default=constants.COUNT_WARNING_THRESHOLD,
                            help='A threshold which, if more than this many '
                                 'ants are seen in 5 seconds, causes the code '
                                 'to output a warning and flag the offending '
                                 'ants.'
                     )
    
    args = args.parse_args()
    if args.sort:
        args.infiles.sort()
    combine_split_track(args.infiles, args.outfile, args.min_duration, args.count_threshold)

if __name__ == '__main__':
    main()

