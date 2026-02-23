import torch
import torchvision
from torchvision.models.detection import FasterRCNN
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.transforms import functional as F
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
from test import iou, get_class_name, nms, prepare_image, get_model
from antsdataset import get_coco_dataset
from torch.utils.data import DataLoader
import json
from collections import defaultdict

def match_predictions_to_gt(pred_boxes, gt_boxes, iou_thresh=0.5):
    matched_gt = set()
    matched_pred = set()

    true_positives = []   
    false_positives = []  
    false_negatives = []  

    for i, pred in enumerate(pred_boxes):
        pred_box = pred[:4]
        best_iou = 0
        best_gt_idx = -1

        for j, gt_box in enumerate(gt_boxes):
            if j in matched_gt:
                continue
            current_iou = iou(pred_box, gt_box)
            if current_iou > best_iou:
                best_iou = current_iou
                best_gt_idx = j

        if best_iou >= iou_thresh:
            true_positives.append(pred)  
            matched_gt.add(best_gt_idx)
            matched_pred.add(i)
        else:
            false_positives.append(pred)

    for j, gt_box in enumerate(gt_boxes):
        if j not in matched_gt:
            false_negatives.append(gt_box)

    return true_positives, false_positives, false_negatives
        

def one_image_compare(image, ground_truth, image_tensor, filename, fig_size=(10, 10)):
    with torch.no_grad():
        prediction = model(image_tensor)
    boxes = prediction[0]['boxes'].cpu().numpy()  
    labels = prediction[0]['labels'].cpu().numpy()  
    scores = prediction[0]['scores'].cpu().numpy()  

    boxes_with_scores = np.hstack([boxes, scores[:, np.newaxis]])

    nms_boxes = nms(boxes_with_scores, iou_threshold=0.3)

    true_pos, false_pos, false_neg = match_predictions_to_gt(nms_boxes, ground_truth, iou_thresh=0.5)

    filtered_fp  = [box[:4] for box in false_pos]
    filtered_tp  = [box[:4] for box in true_pos]
    filtered_fn = [box[:4] for box in false_neg]
    
    threshold = 0.5
    
    plt.figure(figsize=fig_size)  
    plt.imshow(image)  

    # Red Box = False Positive
    for box, label, score in zip(filtered_fp, labels, scores):
        if score > threshold:
            x_min, y_min, x_max, y_max = box
            class_name = get_class_name(label)  # Get the class name
            plt.gca().add_patch(plt.Rectangle((x_min, y_min), x_max - x_min, y_max - y_min, 
                                              linewidth=2, edgecolor='r', facecolor='none'))
            plt.text(x_min, y_min, f"{class_name} ({score:.2f})", color='r')
    
    # Green Box = True Positive
    for box, label, score in zip(filtered_tp, labels, scores):
        if score > threshold:
            x_min, y_min, x_max, y_max = box
            class_name = get_class_name(label)
            plt.gca().add_patch(plt.Rectangle((x_min, y_min), x_max - x_min, y_max - y_min, 
                                              linewidth=2, edgecolor='g', facecolor='none'))
            plt.text(x_min, y_min, f"{class_name} ({score:.2f})", color='g')

    # Blue Box = False Negative
    for box in filtered_fn:
        x_min, y_min, x_max, y_max = box
        plt.gca().add_patch(plt.Rectangle((x_min, y_min), x_max - x_min, y_max - y_min, 
                                              linewidth=2, edgecolor='b', facecolor='none'))
    
    plt.savefig(f"result/lab/{filename}.png")
    plt.close()

def compare_all_images(image_root_dir, ann_file):
    imageDict = defaultdict(list)
    gtDict = defaultdict(list)
    with open(ann_file, 'r') as file:
        data = json.load(file)
        imageData = data["images"]
        annData = data["annotations"]

    for i in range(len(imageData)):
        imageData = data["images"][i]
        imageDict[i] = imageData.get("file_name")
    
    for i in range(len(annData)):
        imageId = annData[i]["image_id"]
        bbox = annData[i]["bbox"]
        x, y, w, h = bbox
        gtDict[imageId].append([x, y, x + w, y + h])
    
    for i in range(len(imageDict)):
        fileName = imageDict[i]
        imagePath = image_root_dir+fileName
        image_tensor = prepare_image(imagePath)
        one_image_compare(Image.open(imagePath), gtDict[i], image_tensor, fileName, fig_size=(10, 10))

if __name__ == "__main__":

    num_classes = 2 # Background + ant


    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')


    model = get_model(num_classes)
    model.load_state_dict(torch.load("trainedModels/fasterrcnn_resnet50_epoch_5.pth"))
    model.to(device)
    model.eval()

    compare_all_images(image_root_dir="ants.v2i.coco-20250708T213721Z-1-001/ants.v2i.coco/test/", ann_file="ants.v2i.coco-20250708T213721Z-1-001/ants.v2i.coco/test/_annotations.coco.json")
    # compare_all_images(image_root_dir="project-1-at-2025-07-02-17-29-a8cd87b5/images/", ann_file="project-1-at-2025-07-02-17-29-a8cd87b5/result.json")

