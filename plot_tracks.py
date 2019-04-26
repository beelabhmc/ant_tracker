import numpy as np
import matplotlib.pyplot as plt
import argparse

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
    plt.title("Distance from Top")
    plt.show()

if __name__== "__main__":
    main()
