from math import cos, sin, pi
import numpy as np
import cv2
import os, os.path

def read_bboxes(filename):
    """Load file and returns a list of the bounding boxes inside.

    Each bounding box is stored as ((upper_left_x, upper_left_y),
    (width, height), angle, *other), where angle is between 0 and π/2
    (radians), and *other lists the other items found in the bbox entry.
    """
    boxes = []
    line = open(filename).read().strip().split()
    for i in range(len(line)):
        box = list(map(float, line[i].split(',')))
        boxes.append(((box[0], box[1]), (box[2], box[3]), box[4])+tuple(box[5:]))
        # file format: [ulx,uly,width,height,angle[,...]* ]+
    return boxes

def get_center(box):
    """Takes a bounding box (formatted as ((upper_left_x, upper_left_y),
    (width, height), angle) and returns the x,y coordinates of the
    center.
    """
    x, y = box[0]
    x += 0.5*(box[1][0]*cos(box[2]) - box[1][1]*sin(box[2]))
    y += 0.5*(box[1][1]*cos(box[2]) + box[1][0]*sin(box[2]))
    return int(x), int(y)

def get_box_vertices(box):
    """Takes a bounding box (formatted as ((upper_left_x, upper_left_y),
    (width, height), angle) and returns a list containing the four
    vertices of the box.
    """
    ulc = np.array(box[0])
    width = box[1][0]*np.array((cos(box[2]), sin(box[2])))
    height = box[1][1]*np.array((-sin(box[2]), cos(box[2])))
    return [ulc, ulc+width, ulc+width+height, ulc+height]

def get_poly_abspos(box):
    """Takes a bounding box and returns its vertices, formatted as a
    list of x,y pairs, relative to the original video.
    """
    return list(zip(map(int, box[3::2]), map(int, box[4::2])))

def get_poly_relpos(box):
    """Takes a bounding box and returns its vertices, formatted as a
    list of x,y pairs relative to the cropped box.
    """
    abspos = get_poly_abspos(box)
    def transform(xy):
        x = xy[0]-box[0][0]
        y = xy[1]-box[0][1]
        return (round(x*cos(box[2])+y*sin(box[2]), 2),
                round(-x*sin(box[2])+y*cos(box[2]), 2))
    return list(map(transform, abspos))

def convert_polygon_to_roi(poly, padding):
    """Takes a polygon and outputs it in ROI format. This consists of a
    list in which the first item is a tuple with the x,y coordinates of
    the upper-left corner of the bounding rectangle, the second is a
    tuple specifying its length and width, and the third is its angle to
    the vertical in radians, between 0 and π/2, measured in radians. The
    fourth item is the polygon which was passed in.

    If padding is specified, then it indicates an extra number of pixels
    to have around all sides of the ROI.
    """
    (x, y), (w, h), angle = cv2.minAreaRect(poly)
    angle = pi/180 * (90+angle)  # Convert to quadrant 1 radians
    w, h = h, w  # swap width and height because angle is changed
    # pad the image
    w += 2*padding
    h += 2*padding
    # Shift x,y from the center (given by cv2) to the corner
    x += -cos(angle)*w/2 + sin(angle)*h/2
    y += -sin(angle)*w/2 - cos(angle)*h/2
    # Round the values to the hundredths so they're easier to look at.
    x, y, w, h, angle = map(lambda x: round(x, 2), [x, y, w, h, angle])
    return [(x, y), (w, h), angle, poly]

def flatten(lst):
    """Flattens a list by taking any iterable element of the list and
    expanding it to be a list of its own.
    """
    out = []
    for item in lst:
        try:
            iter(item)
            out += flatten(item)
        except TypeError:
            out.append(item)
    return out

def save_rois(rois, outfile, imagename):
    if not os.path.isdir(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))
    f = open(outfile, 'w')
    f.write(' '.join(','.join(map(str, flatten(roi))) for roi in rois))
    f.close()

