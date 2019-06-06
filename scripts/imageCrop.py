import csv
import cv2
from matplotlib import pyplot as plt
import math
import glob
import os

import constants
import split


os.chdir(os.getcwd())
for vidName in glob.glob("*.mp4"):
    vidcap = cv2.VideoCapture(vidName)
    success,image = vidcap.read()
    plt.imshow(image, cmap = 'gray', interpolation = 'bicubic')
    plt.xticks([]), plt.yticks([])  # to hide tick values on X and Y axis
    print "Please click"
    coord = plt.ginput(-1)
    if len(coord) % 2 != 0:
        raise Exception("Must choose an even number of coordinates to crop")
    with open('cropped_coordinates.csv', 'a') as csvfile:
        writer = csv.writer(csvfile, delimiter=' ')
        writer.writerow([vidName] + coord)
    split.by_seconds(vidName, 600, extra = '-threads 8')
    os.chdir('split')
    for splitVid in glob.glob("*.mp4"):
        c=0
        for i in range(0, len(coord), 2):
            x, y = coord[i]
            j = i +1
            x2, y2 = coord[j]
            w = math.fabs(x2 - x)
            h = math.fabs(y2 - y)
            rectangle = str(w) +':' + str(h) +':' + str(x) +':'+ str(y) 
            cropName = 'cropped/' + 'crop'+ str(c) +"_"+ splitVid
            command = 'ffmpeg -i ' + splitVid +' -vf "crop=' + rectangle + '" '+ cropName
            os.system(command)
            c+=1
