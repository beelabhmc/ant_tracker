from networkx.algorithms.link_prediction import cn_soundarajan_hopcroft
import os
# os.environ['OPENBLAS_NUM_THREADS'] = '17'  # PLEASE CHANGE ME!

import numpy as np
import cv2
# from numpy.lib.function_base import append
# import sknw
# from skimage.morphology import skeletonize
import matplotlib.pyplot as plt
import matplotlib as mpl
import networkx as nx
# from sklearn.cluster import KMeans
import copy
from cv2 import aruco
import csv
import argparse
from PIL import Image

import bbox

def create_aruco_coords(infile, outfile):
    """
    Inputs
        infile  --  a picture or video file
        outfile --  empty text file
    Outputs
        outfile -- text file with ARTag coordinates for reference image, used as points of reference to apply homography
    """
    try:
        frame = Image.open(infile)
        frame = np.array(frame)
        
    except IOError: 
        print("Not an image, trying as a video file")
        video = cv2.VideoCapture(infile)
        ret, frame = video.read()
        if not ret:
            raise ValueError('Frame not successfully read.')
        

    # Initialize parameters for ARTag detection
    aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_100)
    # aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100) <= newer cv2 version syntax
    parameters = aruco.DetectorParameters_create()
    # parameters = cv2.aruco.DetectorParameters() <= newer cv2 version syntax
    parameters.adaptiveThreshConstant = 20
    parameters.adaptiveThreshWinSizeMax = 20
    parameters.adaptiveThreshWinSizeStep = 6
    parameters.minMarkerPerimeterRate = .02
    parameters.polygonalApproxAccuracyRate = .15
    parameters.perspectiveRemovePixelPerCell = 10
    parameters.perspectiveRemoveIgnoredMarginPerCell = .3
    parameters.minDistanceToBorder = 0

    detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)

    # Find ARTag coordinates in query image and reformat data to match reference coordinates
    # Detect the markers
    # corners, ids, rejectedImgPoints = detector.detectMarkers(frame) <= newer cv2 version syntax
    corners, ids, rejectedImgPoints = aruco.detectMarkers(frame, aruco_dict, parameters=parameters)
    avg = [np.average(x, axis = 1) for x in corners]
    flat_corners = [item for sublist in avg for item in sublist]
    flat_ids = [item for sublist in ids for item in sublist]
    pair = sorted(zip(flat_ids, flat_corners))

    coords = np.array([x[1] for x in pair]).astype(int)
    outfile = open(outfile, "w")
    coords_str = '\n'.join('  '.join(map(str, row)) for row in coords)
    outfile.write(coords_str)
    return outfile

    
def warp(frame, coord1):
    """
    Inputs
        frame -- query image to label
        coord1 -- ARTag coordinates for reference image, used as points of reference to apply homography
    Outputs
        M -- 3x3 transformation matrix, used to warp query image to closely match reference image
        result -- warped query image. We do this warping to consistently label ROIs.
    """
    h, w = frame.shape

    # Initialize parameters for ARTag detection
    aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_100)
    parameters = aruco.DetectorParameters_create()
    parameters.adaptiveThreshConstant = 20
    parameters.adaptiveThreshWinSizeMax = 20
    parameters.adaptiveThreshWinSizeStep = 6
    parameters.minMarkerPerimeterRate = .02
    parameters.polygonalApproxAccuracyRate = .15
    parameters.perspectiveRemovePixelPerCell = 10
    parameters.perspectiveRemoveIgnoredMarginPerCell = .3
    parameters.minDistanceToBorder = 0

    # Find ARTag coordinates in query image and reformat data to match reference coordinates
    corners, ids, rejectedImgPoints = aruco.detectMarkers(frame, aruco_dict, parameters=parameters)
    avg = [np.average(x, axis = 1) for x in corners]
    frame_markers = aruco.drawDetectedMarkers(frame.copy(), corners, ids, [0, 255, 0])
    flat_corners = [item for sublist in avg for item in sublist]
    flat_ids = [item for sublist in ids for item in sublist]
    pair = sorted(zip(flat_ids, flat_corners))

    """
    # Test
    plt.imshow(frame_markers)
    plt.show()"""

    # Warp query image using ARTag coordinates
    coord2 = np.array([x[1] for x in pair]).astype(int)
    print(coord2)

    # WARNING
    # It is possible the number of detect ArUco tags is not 7 (which is the usual)
    # We can still run the pipeline with less than 7, as long as we correctly identify
    # which ArUco tag is missing. Please write software that is able to do so...

    M, _ = cv2.findHomography(coord2, coord1)


    result = cv2.warpPerspective(frame, M, (w,h))
    return M, result

def mask(frame):
    """
    Inputs
        result -- warped query image
    Outputs
        mask -- thresholded query image keeping only bright sections in the image, to isolate the tree
            structure from the background
    """
    thresh = 160 # Might need to adjust this number if lighting conditions call for it (lower for dimmer arenas)
    _, th1 = cv2.threshold(frame,thresh,255,cv2.THRESH_BINARY)

    # Clean up mask with morphological operations
    open_kernel = np.ones((8, 8), np.uint8)
    dilate_kernel = np.ones((6, 6), np.uint8)
    close_kernel = np.ones((6, 6), np.uint8)
    mask = cv2.morphologyEx(th1, cv2.MORPH_OPEN, open_kernel)
    mask = cv2.dilate(mask, dilate_kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, close_kernel)
    return mask

def nodes(mask):
    """
    Inputs
        mask -- thresholded query image
    Outputs
        new_node_centers -- coordinates of each branching point, which is the center of each roi
    """
    # Skeletonize tree and build graph network
    skeleton = skeletonize(mask//255).astype(np.uint16)
    graph = sknw.build_sknw(skeleton)
    nodes = graph.nodes()
    node_centers = np.array([nodes[i]['o'] for i in nodes])

    # Filter out nodes at tips of branches, keeping only nodes that define the centers of each ROI
    copy = graph.copy()
    for i in range(len(node_centers)):
        conn = [n for n in graph.neighbors(i)]
        if len(conn) < 3:
            copy.remove_node(i)
    new_nodes = copy.nodes()
    new_node_centers = np.array([new_nodes[i]['o'] for i in new_nodes]).astype(int)

    return new_node_centers

def centers(reference, ps):
    """
    Inputs
        reference -- coordinates of each roi center in the reference image
        query -- detected coordinates of each roi center in the query image
    Outputs
        newpoints -- reordered query coordinates to match ordering of reference. This allows for consistent
            labelling.
    """
    # Find center point in query that is closest to the center point in reference
    newpoints = []
    for i in range(len(reference)):
        min_dist = 10000
        index = None
        for j in range(len(ps)):
            dist = np.sqrt(np.abs((reference[i][0] - ps[j][0])**2 + (reference[i][1] - ps[j][1])**2))
            if (dist < min_dist):
                min_dist = dist
                index = j
        newpoints.append(ps[index])
    newpoints = np.array(newpoints)
    return newpoints    


# DILATION! CHANGME
def contour(mask):
    """
    Inputs 
        mask -- thresholded query image
    Outputs
        cont -- rather than a skeletonized representation, return a contour image of the tree.
            We will use this to find the vertices of the rois
    """
    # Find and draw only the largest contour in the image. This will be the tree structure
    cont = np.zeros_like(mask)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    contours = max(contours, key=cv2.contourArea)
    cv2.drawContours(cont, contours, -1, [255, 255, 255])

    # Dilate the contours to make the lines thicker
    # kernel = np.ones((3, 3), np.uint8)
    # cont = cv2.dilate(cont, kernel, iterations=1)

    return cont


def vertices(cont, newpoints, Dict, Orientation):
    """
    Inputs
        cont -- contour image of tree structure
        newpoints -- reordered centers of query rois
        Dict -- dictionary mapping current labelling to match lab's labelling
    Outputs
        verts -- vertices of each roi, consistently ordered
    """
    conn = []
    

    for i in range(len(newpoints)):
        cont_test = cont.copy()

        # Points of intersection between circle and contour image represent vertices of an roi
        circle = np.zeros_like(cont)
        cv2.circle(circle, (newpoints[i, 1], newpoints[i, 0]), 40, [255,255,255], 2)

        # # test circle on contour
        # current_directory = os.getcwd()
        # save_location = os.path.join(os.path.join(current_directory, "contour_and_circle"), "the_circles_new_ROI_" + str(Dict[i]) + '.png')
        # print(save_location)
        # cv2.circle(cont_test, (newpoints[i, 1], newpoints[i, 0]), 40, [255,255,255], 2)
        # if not cv2.imwrite(save_location, cont_test):
        #     print("ERROR: Contour and Circle image was not saved")

        inter = cv2.bitwise_and(cont, circle)
        # cv2.imwrite('detect_images/bitwise_' + str(i) + '.png', inter)
        index = np.array(cv2.findNonZero(inter))
        index = np.array([index[i][0] for i in range(len(index))])
        # At times one point of intersection will be detected as two closely positioned points.
        # Use k means to ensure we get the correct number of vertices.
        kmeans = KMeans(n_clusters=6).fit(index)
        centers = np.array(kmeans.cluster_centers_).astype(int)
        # Connect vertices to form a convex polygon
        poly = cv2.convexHull(centers)
        poly = np.array([x[0] for x in poly])

        # Find largest edge defined by the vertices, and reorder vertices so that edge is first
        d = np.diff(poly, axis=0, append=poly[0:1])
        segdists = np.sqrt((d ** 2).sum(axis=1))
        index = np.argmax(segdists)
        roll = np.roll(poly, -index, axis = 0)

        # Reorder right junctions so they have the same labelling as left junctions
        right_set = set()
        for tag, ori in Orientation:
            if ori == "R":
                right_set.add(int(tag))

        if Dict[i] in right_set:
            roll = np.roll(roll, 2, axis = 0)
        conn.append(roll)
        print(i, Dict[i], len(poly))

    conn = np.array(conn)
    
    return conn

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('video',
                            type=str,
                            help='The path to a video with ROIs to detect.',
                           )
    arg_parser.add_argument('outfile',
                            type=str,
                            help='The path to a file in which to write the '
                                 'detected ROIs.',
                           )
    arg_parser.add_argument('-f', '--frame',
                            dest='frame',
                            type=int,
                            default=1,
                            help='The frame number in the video to use for '
                                 'ROI detection (default=1)',
                           )
    arg_parser.add_argument('-y', '--year',
                            dest='year',
                            type=str,
                            help='The year the video was taken',
                           )


    args = arg_parser.parse_args()

    # Read in first frame of video as an image
    if not os.path.isfile(args.video):
        arg_parser.error(f'{args.video} is not a valid file.')

    video = cv2.VideoCapture(args.video)
    ret, frame = video.read()
    if not ret:
        arg_parser.error('The video only has {} frames.'.format(args.frame-1))
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Load in relevant reference coordinates
    coord1 = np.array(np.loadtxt("templates/tag_coordinates.txt")).astype(int)  # Aruco detection (preferably all 7 visible)

    if args.year == "2021":
        reference = np.array(np.loadtxt("templates/center_coordinates_2021.txt")).astype(int)  # Center coordinates. data depends on year
        csv_file = "templates/dictionary_2021.csv"
    elif args.year == "2023":
        reference = np.array(np.loadtxt("templates/center_coordinates_2023.txt")).astype(int)  # Center coordinates. data depends on year
        csv_file = "templates/dictionary_2023.csv"
    elif args.year == "2025":
        reference = np.array(np.loadtxt("templates/center_coordinates_2021.txt")).astype(int)
        csv_file = "templates/dictionary_2025.csv"
        coord1 = "templates/tag_coordinates_2025.txt"


    Dict = {}
    Orientation = []

    with open(csv_file, 'r') as file:
        reader = csv.reader(file)

        # Skip the header
        next(reader)

        # make Dict
        for index, row in enumerate(reader):
            Dict[int(index)] = int(row[0])
            Orientation.append(tuple(row))
    
    M, result = warp(gray, coord1)
    frame_mask = mask(result)
    query = nodes(frame_mask)
    newpoints = centers(reference, query)

    # Testing
    # print(newpoints)
    # for i in range(len(newpoints)):
    #         cv2.circle(result,(newpoints[i][1],newpoints[i][0]),3,[255,0,0],3)
    # plt.imshow(result)
    # plt.show()

    cont = contour(frame_mask)

    # contour picture testing
    current_directory = os.getcwd()
    save_location = os.path.join(current_directory, "contour.png")
    cv2.imwrite(save_location, cont)


    verts = vertices(cont, newpoints, Dict, Orientation)

    # Undo transformation to get vertices coordinates in original frame
    print(verts)
    pts2 = np.array(verts, np.float32)
    polys = np.array(cv2.perspectiveTransform(pts2, np.linalg.pinv(M))).astype(int)


    # Testing
    # print(polys)
    # for i in range(len(polys)):
    #     for j in range(6):
    #         cv2.circle(frame,(polys[i][j][0],polys[i][j][1]),3,[255,0,0],3)
    # plt.imshow(frame)
    # plt.show()

    # Save vertices to outfile
    rois = [bbox.BBox.from_verts(poly, 3) for poly in polys]
    bbox.save_rois(rois, args.outfile)

if __name__ == '__main__':
    # create_aruco_coords(file, outfile)
    main()
