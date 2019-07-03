import os, os.path
import argparse
import re
import math

import bbox

def convert(infile, outfile, bboxes):
    """Loads infile and converts it to which edges were crossed, as
    defined by the bboxes parameter, and then saves it to outfile.
    """
    if not os.path.isdir(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))
    centers = [np.array([w/2, h/2]) for xy, (w, h), *_ in bboxes]
    verts = [np.array(bbox.get_poly_relpos(bboxes[i]))-centers[i]
             for i in range(len(bboxes))]
    offsets = [math.atan2(
    inp = open(infile)
    outp = open(outfile, 'w')
    outp.write('ROI,id,edge0,t0,edge1,t1,number_warning\n')
    outp.write('\n')
    for line in inp:
        roi, idnum, x0, y0, t0, x1, y1, t1, warning = line.split(',')
        roinum = int(re.search(r'[0-9]+', roi).group(0))
        x0 -= centers[roinum][0]
        y0 -= centers[roinum][1]
        a0 = math.atan2(y0, x0) % 2*math.pi
        e0 = 0
        x1 -= centers[roinum][0]
        y1 -= centers[roinum][1]
        e1 = 0
        outp.write(','.join(map(str, [roi, idnum, e0, t0, e1, t1, warning])))
        outp.write('\n')
    outp.close()

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('infile',
                            type=str,
                            help='The file to read data in from.')
    arg_parser.add_argument('outfile',
                            type=str,
                            help='The file to which to write the output.')
    arg_parser.add_argument('roifile',
                            type=str,
                            help='The file from which to load the ROIs.')
    args = arg_parser.parse_args()
    rois = bbox.read_bboxes(roifile)
    convert(args.infile, args.outfile, rois)

if __name__ == '__main__':
    main()

