from math import cos, sin
import numpy as np

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
    return list(zip(map(int, box[5::2]), map(int, box[6::2])))

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

