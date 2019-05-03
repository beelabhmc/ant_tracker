import numpy as np
import matplotlib.pyplot as plt
import argparse

"""
BEWARE:
    An easy pitfall of interpreting these plots is to think the x-axis represents time.
    It doesn't! Each row in the raw_results is an appearance of an ant in a frame, so moments
    when there aren't any ants on the screen are not represented in the plots!
"""

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--i',
                            dest = 'raw_results',
                            required = True,
                            type=str,
                            help='path to some raw coordinate data that we should plot')

    args = arg_parser.parse_args()

    # get the raw results
    # columns are: X_coord, Y_coord, width, height, ant_ID
    data = np.loadtxt(args.raw_results, delimiter=',')
    idL = list(set(data[:, 4]))

    # plt x coords
    for idnum in idL:
        # get tracks for this ant
        antTrack_idx = np.argwhere(data[:, 4] == idnum)
        antTrack = data[data[:, 4] == idnum]
        plt.plot(antTrack_idx, antTrack[:,[0]], label=str(idnum))
    plt.axhline(linestyle='--')
    plt.legend()
    plt.ylabel("Distance")
    plt.xlabel("Frame")
    plt.title("Distance from Left")
    plt.show()

    # plot y coords
    for idnum in idL:
        # get tracks for this ant
        antTrack_idx = np.argwhere(data[:, 4] == idnum)
        antTrack = data[data[:, 4] == idnum]
        plt.plot(antTrack_idx, antTrack[:,[1]], label=str(idnum))
    plt.axhline(linestyle='--')
    plt.legend()
    plt.ylabel("Distance")
    plt.xlabel("Frame")
    plt.title("Distance from Top")
    plt.show()

if __name__== "__main__":
    main()
