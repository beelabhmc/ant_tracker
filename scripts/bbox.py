from math import cos, sin, pi
import numpy as np
import cv2
import os, os.path

class BBox:
    def __init__(self, box, poly, edges=None):
        self._box = box
        self._poly = poly
        self._edges = edges

    @classmethod
    def from_str(cls, string):
        """Creates a new BBox object from the string.

        The format is "ulx,uly,width,height,angle,v1x,v1y,v2x,v2y...:e1,e2,...",
        with the colon and everything after it being optional.
        """
        poly, *edges = string.split(':')
        if edges:
            edges = list(map(int, edges[0].split(',')))
        else:
            edges = None
        poly = poly.split(',')
        poly[:5] = list(map(float, poly[:5]))
        box = ((poly[0], poly[1]), (poly[2], poly[3]), poly[4])
        verts = list(zip(map(int, poly[5::2]), map(int, poly[6::2])))
        return cls(box, verts, edges)

    @classmethod
    def from_verts(cls, verts, padding=0):
        """Takes a list of vertices of a polygon and outputs a
        BBox object with those vertices, and the smallest bounding box
        which fits those vertices.

        If padding is given, the box will have at least padding space
        around the vertices also included.
        """
        (x, y), (w, h), angle = cv2.minAreaRect(verts)
        verts = [tuple(vert) for vert in verts.reshape((-1, 2))]
        angle = pi/180 * (90-angle)  # Convert to radians in quadrant 1
        w, h = h, w
        # Pad the image
        w += 2*padding
        h += 2*padding
        # Shift x,y from center (what OpenCV gives) to upper-left corner
        x += -sin(angle)*w/2 + cos(angle)*h/2
        y += -cos(angle)*w/2 - sin(angle)*h/2
        x, y, w, h, angle = map(lambda x: round(x, 2), (x, y, w, h, angle))
        return cls(((x, y), (w, h), angle), verts)
    
    def __repr__(self):
        """Returns a string which can be passed into the from_str method
        to restore the original image.
        """
        return '%s,%s:%s' % (','.join(map(str, [self.x, self.y, self.w,
                                                self.h, self.a])),
                             ','.join(map(str, list(sum(self.poly_abspos,
                                                        ())))),
                             ','.join(map(str, self.edges)))
    
    def __str__(self):
        return 'BBox:\n\tbox: {}\n\tpoly: {}\n\tedges: {}'\
                    .format(self.box, self.poly, self.edges)

    @property
    def box(self):
        return self._box
    @box.setter
    def box(self, newbox):
        self._box = newbox

    @property
    def edges(self):
        if self._edges is None:
            return [i for i in range(len(self._poly))]
        else:
            return self._edges
    @edges.setter
    def edges(self, newedges):
        self._edges = newedges

    @property
    def x(self):
        return self._box[0][0]

    @property
    def y(self):
        return self._box[0][1]

    @property
    def w(self):
        return self._box[1][0]

    @property
    def h(self):
        return self._box[1][1]

    @property
    def a(self):
        return self._box[2]

    @property
    def center(self):
        """Returns the coordinates of the center of the bounding box.
        """
        return (int(self.x+0.5*self.w*sin(self.a)-0.5*self.h*cos(self.a)),
                int(self.y+0.5*self.h*sin(self.a)+0.5*self.w*cos(self.a)))

    @property
    def poly_abspos(self):
        """Returns the positions of the vertices relative to the
        original video.
        """
        return self._poly

    @property
    def poly_relpos(self):
        """Returns the positions of the vertices relative to the
        bounding box defined.
        """
        def transform(xy):
            x = xy[0]-self.x
            y = xy[1]-self.y
            return (round(x*sin(self.a)+y*cos(self.a), 2),
                    round(-x*cos(self.a)+y*sin(self.a), 2))
        return list(map(transform, self.poly_abspos))
    
    @property
    def box_vertices(self):
        """Returns the vertices of the bounding rectangle, in order
        counter-clockwise from the upper-left one.
        """
        ulc = np.array((self.x, self.y))
        width = self.w*np.array((sin(self.a), cos(self.a)))
        height = self.h*np.array((-cos(self.a), sin(self.a)))
        return [ulc, ulc+height, ulc+width+height, ulc+width]

def read_bboxes(filename):
    """Loads the given file and returns a list of BBox objects for the
    ROIs defined in the file.
    """
    txt = open(filename).read().strip().split()
    return list(map(BBox.from_str, txt))
        
def save_rois(rois, outfile):
    if not os.path.isdir(os.path.dirname(os.path.abspath(outfile))):
        os.makedirs(os.path.dirname(os.path.abspath(outfile)))
    f = open(outfile, 'w')
    f.write(' '.join(map(repr, rois)))
    f.close()

