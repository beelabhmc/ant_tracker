import argparse
import os
import re

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--f',
                            dest = 'ROI',
                            required = True,
                            type=str,
                            help='a txt file of the bounding boxes for ROI')
    arg_parser.add_argument('--r',
                            dest = 'label',
                            required = True,
                            type=str,
                            help='the name of the roi_label you\'d like to crop')
    arg_parser.add_argument('--i',
                            dest = 'splitVid',
                            required = True,
                            type=str,
                            help='path to a video to crop')
    arg_parser.add_argument('--o',
                            dest = 'outVid',
                            required = True,
                            type=str,
                            help='path of video to output')
    arg_parser.add_argument('--l',
                            dest = 'logFile',
                            type=str,
                            default="/dev/null",
                            help='path to log file')
    args = arg_parser.parse_args()

    """
        read ROI labels from txt into a dictionary
        dict keys will be tuples containing
            1) the path to the frame that was used
            2) the ROI label name
        dict values will be lists containing the coords of the box
    """
    print("Reading boxes from "+args.ROI)
    bboxes={}
    f = open(args.ROI, 'r')
    # get the ROI label names (separated by tabs)
    names = f.readline().strip().split("\t")[1:]
    names = [re.sub("_1$", "", x) for x in names]
    c=0
    for line in f:
        # get ROI coords and path to frame
        line = line.strip().split("\t")
        filePath = os.path.abspath(os.path.splitext(line[0])[0])
        numbers = line[1:]
        numbers = [int(x) if x else None for x in numbers]
        for i in range(0, len(numbers), 4):
            if numbers[i]:
                # save filepath and ROI name as keys for the ROI coords
                bboxes[(filePath, names[i])] = numbers[i:(i+4)]
    f.close()


    """
        split videos into 10 min segments then crop into boxes
        according to the coordinates provided in ROI
    """
    # get path to video
    splitVid = os.path.abspath(args.splitVid)
    # crop each video
    # boxNm should be a tuple containing the absolute path to the frame
    #     that was used, as well as the ROI label name
    # filter just the box we want
    boxNames = filter(lambda boxNm: os.path.basename(boxNm[0]) \
                          == os.path.splitext(os.path.basename(splitVid))[0] \
                          and boxNm[1] == args.label, bboxes.keys())
    for boxNm in boxNames:
        # get the coords for this box
        boxCoord = bboxes[boxNm]
        x = float(boxCoord[0])
        y = float(boxCoord[1])
        w = boxCoord[2]
        h = boxCoord[3]
        # call ffmpeg with the coords to actually do the work of cropping the video
        rectangle = str(w) +':' + str(h) +':' + str(x) +':'+ str(y)
        print("Attempting to create cropped output: " + args.outVid)
        # this uses a simple filtergraph to crop the video (type "man
        # ffmpeg" in the terminal for more info)
        # we use the -y option to force overwrites of output files
        # we use the max_muxing_queue_size to resolve "Too many packets
        # buffered for output stream" errors
        # also the loglevel option to disable any ffmpeg output that
        # isn't an error/warning
        command = 'ffmpeg -y -loglevel warning -i ' + splitVid +' -vf "crop=' \
                  + rectangle + '" -max_muxing_queue_size 10000 '+ args.outVid \
                  + ' >>' + args.logFile + ' 2>&1'
        os.system(command)

if __name__== "__main__":
    main()

