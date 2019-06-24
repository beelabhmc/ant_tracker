from math import cos, sin
import numpy as np

def read_bboxes(filename):
    """Load file and returns a list of the bounding boxes inside.

    Each bounding box is stored as ((upper_left_x, upper_left_y),
    (width, height), angle), where angle is between 0 and π/2 (radians).
    """
    boxes = []
    line = open(filename).read().strip().split()
    for i in range(len(line)):
        box = list(map(float, line[i].split(',')))
        boxes.append(((box[0], box[1]), (box[2], box[3]), box[4]))
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

def get_vertices(box):
    """Takes a bounding box (formatted as ((upper_left_x, upper_left_y),
    (width, height), angle) and returns a list containing the four
    vertices of the box.
    """
    ulc = np.array(box[0])
    width = box[1][0]*np.array((cos(box[2]), sin(box[2])))
    height = box[1][1]*np.array((-sin(box[2]), cos(box[2])))
    return [ulc, ulc+width, ulc+width+height, ulc+height]


