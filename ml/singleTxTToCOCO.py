from txtToCOCO import create_annotation, create_image
from pathlib import Path
import os
from natsort import natsorted
import json
import argparse

# Lots of code duplication from the other singe combine when you have time
def get_args():
    parser = argparse.ArgumentParser("txt to COCO dataset format")
    parser.add_argument(
        "-p",
        "--path",
        nargs=2,
        metavar=('TEXTPATH', 'IMAGEPATH'),
        type=str,
        help="Absolute path for image and annotation text files in that order",
    )
    parser.add_argument(
        "-b",
        "--bbox",
        nargs=4,
        metavar=("xmin, ymin, xmax, ymax"),
        type=int,
        help="word location in the line for the xmin, ymin, xmax, ymax location in the txt"
    )
    parser.add_argument(
         "-i",
         "--image",
         type = int,
         help = "location of the image index"
    )

    parser.add_argument(
        "-o",
        "--output",
        type = str,
        help="Absolute path for the output location of the json file"
    )
    return parser.parse_args()

def main(arg):
    txt_filepath, image_filepaths = arg.path
    annotations = []
    l1, l2, l3, l4 = arg.bbox
    l0 = arg.image
    with open(txt_filepath, "r") as file:
        for id, line in enumerate(file):
            spiltList = line.split(",")
            image_id = int(spiltList[l0])
            x,y,h,w = float(spiltList[l1]), float(spiltList[l2]), float(spiltList[l3]), float(spiltList[l4])
            bbox = [x, y, h, w]
            annotation = create_annotation(id, image_id, bbox)
            annotations.append(annotation)

    im_path = Path(image_filepaths)

    id = 1
    images = []
    if im_path.is_dir():
            im_file_paths = natsorted(im_path.rglob("*.jpg"))
            im_file_paths += natsorted(im_path.rglob("*.jpeg"))
            im_file_paths += natsorted(im_path.rglob("*.png"))

    for filepath in im_file_paths:
        name = os.path.basename(filepath)
        image = create_image(name, id)
        images.append(image)
        id += 1

    # print(annotations)
    # print(images)

    coco_data = {}
    coco_data["images"] = images
    coco_data["annotations"] = annotations
    output_name = arg.output 
    with open(output_name, 'w') as outfile:
        json.dump(coco_data, outfile, indent=4)

if __name__ == "__main__":
    arguments = get_args()
    main(arguments)