import torch
import torchvision
from torchvision.models.detection import FasterRCNN
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
import numpy as np
from antsdataset import get_coco_dataset
from torch.utils.data import DataLoader
from test import iou, nms, get_model
from collections import defaultdict

def calculate_mAP(det_dict, gt_dict, iou_threshold=0.5):

    gt_matched = {}
    total_true_bboxes = 0
    for image_id, gts in gt_dict.items():
        gt_matched[image_id] = [False] * len(gts)
        total_true_bboxes += len(gts)

    all_detections = []
    for image_id, det_lists in det_dict.items():
        for det_array in det_lists:
            for det in det_array:
                all_detections.append((image_id, det))

    if total_true_bboxes == 0:
        return 0.0  

    all_detections.sort(key=lambda x: x[1][4], reverse=True)

    tp = []
    fp = []

    for image_id, det in all_detections:
        pred_box = det[:4]
        best_iou = -1
        best_gt_idx = -1

        for gt_idx, gt_box in enumerate(gt_dict.get(image_id, [])):
            iou_value = iou(pred_box, gt_box)
            if iou_value > best_iou:
                best_iou = iou_value
                best_gt_idx = gt_idx

        if best_iou >= iou_threshold and not gt_matched[image_id][best_gt_idx]:
            tp.append(1)
            fp.append(0)
            gt_matched[image_id][best_gt_idx] = True
        else:
            tp.append(0)
            fp.append(1)

    tp = np.cumsum(tp)
    fp = np.cumsum(fp)

    eps = np.finfo(np.float32).eps
    recalls = tp / np.maximum(total_true_bboxes, eps)
    precisions = tp / np.maximum((tp + fp), eps)

    recalls = np.concatenate(([0.0], recalls, [1.0]))
    precisions = np.concatenate(([0.0], precisions, [0.0]))

    ap = 0.0
    for interp_pt in np.arange(0, 1.0001, 0.1):
        precs = precisions[recalls >= interp_pt]
        if precs.size > 0:
            ap += precs.max()
    ap = ap / 11.0
    return ap


def evaluate_mAP(model, data):

    device = torch.device('cuda')

    # two classes: background + ant
    # model = get_model(2)
    # model.load_state_dict(torch.load(f"ml/trainedModels/fasterrcnn_resnet50_epoch_{num_epochs}.pth"))
    model.to(device)
    model.eval()
    
    # dictionary of lists that contains all of the bbox by image_id
    # x1, y1, x2, y2
    gt_boxes = defaultdict(list)
    det_boxes = defaultdict(list)

    for images, targets in data:

        images = [img.to(device) for img in images]
        predictions = model(images)

        for idx, target in enumerate(targets):

            image_id = None
            for obj in target:
                
                bbox = obj["bbox"]  # Coco Format: [x, y, width, height]
                x, y, w, h = bbox
                
                # Change this default value
                image_id = obj.get("image_id", image_id)


                if w > 0 and h > 0:
                    gt_boxes[image_id].append([x, y, x + w, y + h])

            with torch.no_grad():
                pred = predictions[idx]
                boxes = pred.get("boxes").cpu()
                scores = pred.get("scores").cpu()

                if boxes.size == 0:
                    print("No Detections")
                    continue
                
                boxes_with_scores = np.hstack([boxes, scores[:, np.newaxis]])
                nms_boxes = nms(boxes_with_scores, iou_threshold=0.3)
                det_boxes[image_id].append(nms_boxes)
    
    ap = calculate_mAP(det_boxes, gt_boxes, iou_threshold=0.5)
    print(ap)
    return ap

# if __name__ == "__main__":

#     num_classes = 2 # Background + ant


#     device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')

#     val_dataset = get_coco_dataset(
#         # img_dir="/Users/pk_3/My_Documents/AntProjectSM2025/ant_tracker-1/ml/ants.v2i.coco/valid",
#         # ann_file="/Users/pk_3/My_Documents/AntProjectSM2025/ant_tracker-1/ml/ants.v2i.coco/valid/_annotations.coco.json"
#         # img_dir="/Users/pk_3/My_Documents/AntProjectSM2025/ant_tracker-1/ml/natural_substrate/test/images",
#         # ann_file="/Users/pk_3/My_Documents/AntProjectSM2025/ant_tracker-1/ml/natural_substrate/test/images/annotations.coco.json"
#         # img_dir="/home/paulkim/Documents/BeeLabSM2025/ml-ant_tracker/ant_tracker/ml/ants.v2i.coco-20250708T213721Z-1-001/ants.v2i.coco/valid",
#         # ann_file="/home/paulkim/Documents/BeeLabSM2025/ml-ant_tracker/ant_tracker/ml/ants.v2i.coco-20250708T213721Z-1-001/ants.v2i.coco/valid/_annotations.coco.json"
#         # img_dir="/home/paulkim/Documents/BeeLabSM2025/ml-ant_tracker/ant_tracker/ml/Ant_dataset/OutdoorDataset/Seq0006Object21Image64/img",
#         # ann_file="/home/paulkim/Documents/BeeLabSM2025/ml-ant_tracker/ant_tracker/ml/Ant_dataset/OutdoorDataset/Seq0006Object21Image64/annotations.coco.json"
#         img_dir="/home/paulkim/Documents/BeeLabSM2025/ml-ant_tracker/ant_tracker/ml/export_176945_project-176945-at-2025-07-30-22-46-72354786/images",
#         ann_file="/home/paulkim/Documents/BeeLabSM2025/ml-ant_tracker/ant_tracker/ml/export_176945_project-176945-at-2025-07-30-22-46-72354786/cleanresult.json"
#     )

#     val_loader = DataLoader(val_dataset, batch_size=4, shuffle=False, collate_fn=lambda x: tuple(zip(*x)))



#     model = get_model(num_classes)
#     model.load_state_dict(torch.load("ml/trainedModels/fasterrcnn_resnet50_epoch_10.pth"))
#     model.to(device)
#     model.eval()  

#     # Not sure if this is needed
#     COCO_CLASSES = {0: "Background", 1: "Ant"}

#     evaluate_mAP(val_loader)