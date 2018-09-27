from constants import *
import re

def getBBox(ROI_fileName):
    bboxes={}
    file = open(DIRECTORY+ROI_fileName, 'r')
    names = file.readline().strip().split(",")[1:]
    names = [re.sub("_1", "", x) for x in names]
    c=0
    for line in file:
        line = line.strip().split(",")
        filePath = line[0].split("/")[-1].split('.')[0]
        numbers = line[1:]
        numbers = [int(x) if x else None for x in numbers]
        for i in range(0, len(numbers), 4):
            if numbers[i]:
                bboxes[(filePath, names[i])] = numbers[i:(i+4)]
    file.close()
    print(bboxes)
    return bboxes

