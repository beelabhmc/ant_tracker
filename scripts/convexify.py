import numpy as np

def convexify(verts):
    """Takes the vertices and returns the vertices of the convex hull
    of the polygon defined by these vertices. It is assumed that the
    vertices are in counter-clockwise order.

    The algorithm which I use originates from Lee 1983 (On Finding the
    Convex Hull of a Simple Polygon), and runs in quadratic time and 
    linear space on the size of the input.
    The one in the paper is linear both, but takes the vertices as a
    linked list. Performance could be increased by doing that, but I
    doubt this function will ever be called on a huge number of vertices
    so I am not doing this conversion.

    The paper can be found here (hopefully no dead links):
    https://link.springer.com/content/pdf/10.1007%2FBF00993195.pdf
    """
    verts = list(verts.reshape(-1, 2))
    # Find v_0 from which to start
    # Negative vertices are so that we can count from the end
    m = -len(verts)
    for i in range(-1, -len(verts)+1, -1):
        if verts[i][1] < verts[m][1] or \
                verts[i][1] == verts[m][1] and verts[i][0] < verts[m][0]:
            m = i
    i = m+2
    retain = [verts[m], verts[m+1]]
    while any(verts[i] != retain[0]):
        s = compute_s_value(retain[-1], retain[-2], verts[i])
        print(retain, s, verts[i])
        if s <= 0:
            # verts[i] is to the right of the previous edge
            while len(retain) > 1 and \
                    compute_s_value(retain[-1], retain[-2], verts[i]) <= 0:
                retain.pop()
            retain.append(verts[i])
            i += 1
        else:
            if not is_degenerate_handle(retain[-2], retain[-1], verts):
                if winding_number(verts[i],
                                  get_lobe(retain[-2], retain[-1], verts)):
                    continue
            if compute_s_value(retain[-1], retain[0], verts[i]) > 0:
                retain.append(verts[i])
            i += 1;
    return np.array(retain).reshape(-1, 1, 2)

def is_degenerate_handle(v0, v1, verts):
    """Returns True iff v0->v1 is an edge in verts."""
    return all(verts[(index(verts, v0)+1) % len(verts)] == v1)

def compute_s_value(v0, v1, v2):
    """Computes the s parameter as defined in Section 2 of Lee 1983."""
    return v2[1]*(v1[0]-v0[0]) - v2[0]*(v1[1]-v0[1]) + v0[0]*v1[1]-v0[1]*v1[0]

def get_lobe(v0, v1, verts):
    """Returns the lobe defined by v0 and v1 as a list of vertices in
    their original order in verts.
    """
    start = index(verts, v0)
    end = index(verts, v1)
    if start < end:
        return verts[start:end+1]
    else:
        return verts[start-len(verts):end+1]

def quadrant(x, y):
    """Returns which quadrant (x, y) is in, with Q1 being upper-right
    and the quadrants continuing CCW.
    """
    if x >= 0:
        if y >= 0:
            return 1
        return 4
    if y >= 0:
        return 2
    return 3

def winding_number(v, poly):
    """Computes the number of times poly winds around v.
        If 0, v is outside of poly.
        If nonzero, v is inside of poly.
        If greater than 1, v is inside some locally non-simple region.
        If negative, then poly's vertices are clockwise
    poly is assumed to be counter-clockwise unless otherwise specified
    """
    prev = quadrant(*(poly[0]-v))
    wn = 0
    for vert in poly[1:] + [poly[0]]:
        curr = quadrant(*(vert-v))
        if curr == 1 and prev == 4:
            wn += 1
        if curr == 4 and prev == 1:
            wn -= 1
        prev = curr
    return wn

def index(lst, nparr):
    for i in range(len(lst)):
        if all(nparr == lst[i]):
            return i
    return -1

