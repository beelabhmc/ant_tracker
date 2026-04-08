import torch
from torchvision.ops import box_iou


def calculate_mAP(pred_boxes, pred_scores, pred_labels, gt_boxes, gt_labels, iou_threshold=0.6):
    # """
    # Calculate Average Precision at a given IoU threshold.
    # A detection is correct if IoU >= iou_threshold (default 0.6 = 60% overlap).
    # """
    if len(pred_boxes) == 0 and len(gt_boxes) == 0:
        return 1.0  # No predictions, no ground truth = perfect
    if len(pred_boxes) == 0:
        return 0.0  # No predictions but has ground truth = 0
    if len(gt_boxes) == 0:
        return 0.0  # Predictions but no ground truth = 0 (all false positives)
    
    # Sort predictions by score (descending)
    sorted_indices = torch.argsort(pred_scores, descending=True)
    pred_boxes = pred_boxes[sorted_indices]
    pred_labels = pred_labels[sorted_indices]
    
    # Calculate IoU between all predictions and ground truths
    ious = box_iou(pred_boxes, gt_boxes)
    
    # Match predictions to ground truths
    num_preds = len(pred_boxes)
    num_gt = len(gt_boxes)
    tp = torch.zeros(num_preds)
    fp = torch.zeros(num_preds)
    gt_matched = torch.zeros(num_gt, dtype=torch.bool)
    
    for i in range(num_preds):
        pred_label = pred_labels[i]
        
        # Find best matching ground truth (same class, highest IoU, not yet matched)
        best_iou = 0.0
        best_gt_idx = -1
        
        for j in range(num_gt):
            if gt_matched[j]:
                continue  # Already matched
            if pred_label != gt_labels[j]:
                continue  # Different class
            
            current_iou = ious[i, j].item()
            if current_iou > best_iou:
                best_iou = current_iou
                best_gt_idx = j
        
        # Check if IoU >= threshold (60% overlap)
        if best_iou >= iou_threshold and best_gt_idx >= 0:
            tp[i] = 1  # True positive
            gt_matched[best_gt_idx] = True
        else:
            fp[i] = 1  # False positive
    
    # Calculate precision and recall at each threshold
    tp_cumsum = torch.cumsum(tp, dim=0)
    fp_cumsum = torch.cumsum(fp, dim=0)
    
    precision = tp_cumsum / (tp_cumsum + fp_cumsum + 1e-10)
    recall = tp_cumsum / (num_gt + 1e-10)
    
    # Add (0, 1) point for proper AP calculation
    precision = torch.cat([torch.tensor([1.0]), precision])
    recall = torch.cat([torch.tensor([0.0]), recall])
    
    # Calculate AP using trapezoidal rule
    ap = torch.trapezoid(precision, recall).item()
    
    return max(0.0, min(1.0, ap))  # Clamp to [0, 1]


def evaluate_mAP(model, data_loader, iou_threshold=0.6, score_threshold=0.5):
    # """
    # Evaluate model on a dataloader and return mAP.
    
    # Args:
    #     model: The detection model
    #     data_loader: DataLoader with (images, targets)
    #     iou_threshold: IoU threshold for correct detection (default 0.6 = 60%)
    #     score_threshold: Minimum confidence score for predictions
    
    # Returns:
    #     float: mean Average Precision
    # """
    device = next(model.parameters()).device
    model.eval()
    
    all_aps = []
    total_tp = 0
    total_fp = 0
    total_gt = 0
    
    with torch.no_grad():
        for images, targets in data_loader:
            images = [img.to(device) for img in images]
            
            # Get predictions
            predictions = model(images)
            
            for pred, target in zip(predictions, targets):
                # Filter predictions by score threshold
                mask = pred['scores'] >= score_threshold
                pred_boxes = pred['boxes'][mask]
                pred_scores = pred['scores'][mask]
                pred_labels = pred['labels'][mask]
                
                # Process ground truth from COCO format
                gt_boxes = []
                gt_labels = []
                for obj in target:
                    bbox = obj["bbox"]  # Format: [x, y, width, height]
                    x, y, w, h = bbox
                    if w > 0 and h > 0:
                        gt_boxes.append([x, y, x + w, y + h])  # Convert to [x_min, y_min, x_max, y_max]
                        gt_labels.append(obj["category_id"])
                
                if len(gt_boxes) == 0 and len(pred_boxes) == 0:
                    all_aps.append(1.0)  # Both empty = perfect
                    continue
                elif len(gt_boxes) == 0:
                    all_aps.append(0.0)  # No GT but has predictions = all FP
                    total_fp += len(pred_boxes)
                    continue
                
                gt_boxes = torch.tensor(gt_boxes, dtype=torch.float32).to(device)
                gt_labels = torch.tensor(gt_labels, dtype=torch.int64).to(device)
                
                total_gt += len(gt_boxes)
                
                if len(pred_boxes) == 0:
                    all_aps.append(0.0)  # Has GT but no predictions
                    continue
                
                # Calculate AP for this image with 60% IoU threshold
                ap = calculate_mAP(
                    pred_boxes, pred_scores, pred_labels,
                    gt_boxes, gt_labels, 
                    iou_threshold=iou_threshold
                )
                all_aps.append(ap)
    
    if len(all_aps) == 0:
        return 0.0
    
    mean_ap = sum(all_aps) / len(all_aps)
    print(f"Evaluated {len(all_aps)} images, mAP@{iou_threshold}: {mean_ap:.4f}")
    
    return mean_ap