import os
from pathlib import Path
from natsort import natsorted
import json
import argparse

#txt_filepath = "/Users/pk_3/My_Documents/AntProjectSM2025/ant_tracker-1/ml/natural_substrate/train/bboxes"
#image_filepaths = "/Users/pk_3/My_Documents/AntProjectSM2025/ant_tracker-1/ml/natural_substrate/train/images"
# 0 1 2 3
#output file = /Users/pk_3/My_Documents/AntProjectSM2025/ant_tracker-1/ml/natural_substrate/train/images/annotations.coco.json

def create_annotation(
    id,
    image_id,
    bbox
):
  annotation = {"id": id, "image_id":image_id, "category_id": 1, "bbox": bbox}
  return annotation

def create_image(
    filename,
    id
):
  image = {"file_name": filename, "id": id}
  return image

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
        "-o",
        "--output",
        type = str,
        help="Absolute path for the output location of the json file"
    )
    return parser.parse_args()

def main(args):
    txt_filepath, image_filepaths = args.path
    txt_path = Path(txt_filepath)
    if txt_path.is_dir():
        txt_file_paths = natsorted(txt_path.rglob("*.txt"))
    annotations = []
    id = 0
    image_id = 0
    for filepath in txt_file_paths:
        with open(filepath, 'r') as f:
            for x in f:
                splitList = x.split()
                l1, l2, l3, l4 = args.bbox
                xmin, ymin, xmax, ymax = int(splitList[l1]), int(splitList[l2]), int(splitList[l3]), int(splitList[l4])
                bbox = [xmin, ymin, xmax - xmin, ymax - ymin] # in COCO bbox format [x,y,width,height]
                annotation = create_annotation(id, image_id, bbox)
                annotations.append(annotation)
                id += 1
        image_id += 1

    im_path = Path(image_filepaths)
    if im_path.is_dir():
            im_file_paths = natsorted(im_path.rglob("*.jpg"))
            im_file_paths += natsorted(im_path.rglob("*.jpeg"))
            im_file_paths += natsorted(im_path.rglob("*.png"))

    id = 0
    images = []
    for filepath in im_file_paths:
        name = os.path.basename(filepath)
        image = create_image(name, id)
        images.append(image)
        id += 1

    coco_data = {}
    coco_data["images"] = images
    coco_data["annotations"] = annotations
    output_name = args.output
    with open(output_name, 'w') as outfile:
        json.dump(coco_data, outfile, indent=4)

if __name__ == "__main__":
    arguments = get_args()
    main(arguments)