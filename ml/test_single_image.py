import torch
import torchvision
from torchvision.models.detection.faster_rcnn import (
    FastRCNNPredictor,
    FasterRCNN_ResNet50_FPN_V2_Weights,
)
from PIL import Image, ImageDraw, ImageFont
import torchvision.transforms.functional as F
from pathlib import Path
import numpy as np


def get_model(num_classes):
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn_v2(
        weights=FasterRCNN_ResNet50_FPN_V2_Weights.DEFAULT
    )
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
    return model


def test_on_image(
    image_path,
    model_path="/home/livia/Desktop/model.pth",
    output_dir="result",
    score_threshold=0.3,
):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Load model
    num_classes = 2
    model = get_model(num_classes)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    print(f"Loaded model from: {model_path}")
    
    # Load image
    image_path = Path("/home/livia/AntTrack/ant_tracker/input/anttest2.JPG")
    if not image_path.exists():
        # Try looking in common locations
        possible_paths = [
            Path("/home/livia/AntTrack/ant_tracker/ml") / image_path.name,
            Path("/home/livia/AntTrack/ant_tracker") / image_path.name,
            Path("/home/livia/Desktop") / image_path.name,
            Path("/home/livia") / image_path.name,
        ]
        for p in possible_paths:
            if p.exists():
                image_path = p
                break
        else:
            print(f"ERROR: Could not find image: {image_path}")
            return
    
    print(f"Loading image: {image_path}")
    image = Image.open(image_path).convert("RGB")
    image_tensor = F.to_tensor(image).to(device)
    
    # Run inference
    with torch.no_grad():
        outputs = model([image_tensor])[0]
    
    boxes = outputs['boxes'].cpu().numpy()
    scores = outputs['scores'].cpu().numpy()
    labels = outputs['labels'].cpu().numpy()
    
    print(f"\nTotal detections: {len(boxes)}")
    print(f"Detections with score > {score_threshold}: {(scores >= score_threshold).sum()}")
    
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Draw annotations on image
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    detection_count = 0
    for box, score, label in zip(boxes, scores, labels):
        if score >= score_threshold:
            detection_count += 1
            x1, y1, x2, y2 = box
            
            # Color based on confidence: green for high, yellow for medium, red for low
            if score >= 0.7:
                color = "green"
            elif score >= 0.5:
                color = "yellow"
            else:
                color = "red"
            
            # Draw bounding box
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
            
            # Draw label with score
            text = f"{score:.2f}"
            
            # Draw text background
            text_bbox = draw.textbbox((x1, y1 - 20), text, font=font)
            draw.rectangle(text_bbox, fill=color)
            draw.text((x1, y1 - 20), text, fill="black", font=font)
            
            # Draw center point
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            r = 3
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="white", outline=color)
    
    # Save annotated image
    output_path = output_dir / f"annotated_{image_path.stem}_thresh{score_threshold}.jpg"
    image.save(output_path)
    print(f"\nSaved annotated image to: {output_path}")
    print(f"Detected {detection_count} ants (score > {score_threshold})")
    
    # Legend
    print("\nColor legend:")
    print("  Green: score >= 0.7 (high confidence)")
    print("  Yellow: 0.5 <= score < 0.7 (medium confidence)")
    print("  Red: 0.3 <= score < 0.5 (low confidence)")
    
    # Show all detections with scores
    print(f"\nAll {detection_count} detections (sorted by score):")
    sorted_indices = np.argsort(scores)[::-1]
    for i, idx in enumerate(sorted_indices):
        if scores[idx] >= score_threshold:
            box = boxes[idx]
            score = scores[idx]
            print(f"  {i+1}. score={score:.3f}, box=[{box[0]:.1f}, {box[1]:.1f}, {box[2]:.1f}, {box[3]:.1f}]")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test model on a single image")
    parser.add_argument("--image", type=str, default="input_anttest2.JPG",
                        help="Path to input image")
    parser.add_argument("--model", type=str, default="/home/livia/Desktop/model.pth",
                        help="Path to saved model weights")
    parser.add_argument("--output", type=str, default="result",
                        help="Output directory for results")
    parser.add_argument("--threshold", type=float, default=0.3,
                        help="Score threshold for detections")
    
    args = parser.parse_args()
    
    test_on_image(
        image_path=args.image,
        model_path=args.model,
        output_dir=args.output,
        score_threshold=args.threshold,
    )