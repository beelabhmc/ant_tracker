import cv2
import matplotlib.pyplot as plt
import argparse

def roi_poly_input(video, show_image=False):
    if not os.path.isfile(video):
        raise RuntimeError(f'{video} is not a file.')
    if show_image:
        ret, img = cv2.VideoCapture(video).read()
        if not ret:
            raise RuntimeError(f'Unknown error reading {video}')
        plt.imshow(cv2.cvtColor(img, cv2.RGB2BGR))
        plt.draw()
    num_rois = int(input('How many ROIs are in this video? '))
    rois = []
    for i in range(num_rois):
        pts = []
        prompt = 'Please input x,y coordinates of the next point, separated ' \
                 'by a comma, or an empty string to save this ROI.'
        while True:
            line = input(prompt)
            if line == '':
                break
            try:
                x, y = map(float, line.split(','))
                pts.append((x, y))
            except:
                print('Could not read input. Please try again.')
                continue
        box = bbox.convert_poly_to_roi(np.array(pts).reshape((-1, 1, 2)), 2)
        rois.append(box)
    return rois

def roi_rect_input(videos, show_image=False):
    if not os.path.isfile(video):
        raise RuntimeError(f'{video} is not a file.')
    if show_image:
        ret, img = cv2.VideoCapture(video).read()
        if not ret:
            raise RuntimeError(f'Unknown error while reading {video}')
        plt.imshow(cv2.cvtColor(img, cv2.RGB2BGR))
        plt.draw()
    num_rois = int(input('How many ROIs are in this video? '))
    rois = []
    while len(rois) < num_rois:
        try:
            ax, ay = map(float, input('Please input coordinates of upper-' \
                               'left vertex, separated by a comma').split(','))
            bx, by = map(float, input('Please input coordinates of lower-' \
                               'right vertex, separated by a comma').split(','))
            cx, cy = map(float, input('Please input coordinates of lower-' \
                               'left vertex, separated by a comma').split(','))
        except:
            print('Could not read input. Please try again.')
            continue
        # Rectangles form a 5-dimensional vector space (R^4 ⨉ R/πR, to be
        # precise), while the user just inputted 3 points, each of which
        # are two-dimensional (R^2). Thus, the user inputted 6 dimensions
        # of data and we need to reduce it to 5.
        # The simplest approach would be to trust the user to input a
        # valid set of points for a rectangle. However, I do not trust
        # end users to have that level of precision with their
        # specifications.
        # Therefore, I'm assuming that the true lower-right corner vertex
        # lies along the line specified by the upper left and lower right
        # vertices, but allowing it to move along that line to reduce the
        # number of dimensions to which the rectangle must match to 5, as
        # there should be exactly one rectangle which matches.
        # Here, you see a bunch of algebra which the computer does to
        # perform that moving of the lower-right vertex. You shouldn't
        # have to ever mess with this code below here.
        # TODO make this robust against perfectly horizontal/vertical
        # rectangles
        b1 = ay - (by-ay) / (bx-ax)*ax
        b2 = cy + (ax-cx) / (ay-cy)*cx
        m1 = (by-ay) / (bx-ax)
        m2 = - (cx-ax) / (cy-ay)
        bx = - (b2 - b1) / (m2 - m1)
        by = b1 + m1*bx
        # And now we need to convert these rectangles into the format
        # which the ROI saving function works in
        dx, dy = ax + bx-cx, ay + by-cy
        pts = [(ax, ay), (cx, cy), (bx, by), (dx, dy)]
        x, y = ax, ay
        w, h = ((cx-ax)**2+(cy-ay)**2)**.5, ((cx-bx)**2+(cy-by)**2)**.5
        angle = math.atan((ax-cx) / (ay-cy))
        rois.append([(x, y), (w, h), angle] + pts)
    return rois

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('infile',
                            type='str',
                            help='The path to the video to read.')
    arg_parser.add_argument('outfile',
                            type='str',
                            help='The file to which to write the rois.')
    arg_parser.add_argument('--no-polys',
                            default=False,
                            const=True,
                            action='store_const',
                            help='Do not input polygons, only rectangular '
                                 'bboxes.')
    args = arg_parser.parse_args()
    rois = roi_poly_input(args.infile)
    bbox.save_rois(rois, args.outfile, args.infile)

