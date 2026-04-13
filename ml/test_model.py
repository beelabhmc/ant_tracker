import torch
from pathlib import Path
from torch.utils.data import DataLoader, ConcatDataset
import sys
sys.path.append(str(Path(__file__).parent))

from train_copy2 import get_model
from antsdataset import get_coco_dataset
from valid_updated import evaluate_mAP


def test_saved_model(model_path="/home/livia/Desktop/model_updated.pth", iou_threshold=0.3):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Load the saved model
    num_classes = 2
    model = get_model(num_classes)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    
    print(f"Loaded model from: {model_path}")
    
    # Load test datasets
    test_dirs = [
        "project-3-at-2026-03-13-18-57-9ddf8827",
    ]
    
    base_dir = Path(__file__).parent
    test_datasets = []
    
    for test_dir in test_dirs:
        # Find the annotation file
        matches = list(base_dir.rglob(f"*{test_dir}*/*annotations*.json"))
        if not matches:
            matches = list(base_dir.rglob(f"*{test_dir}*"))
            for m in matches:
                ann_matches = list(m.rglob("*annotations*.json"))
                if ann_matches:
                    matches = ann_matches
                    break
        
        if matches:
            ann_file = matches[0]
            img_dir = ann_file.parent / "images"
            if not img_dir.exists():
                img_dir = ann_file.parent
            
            print(f"Loading test dataset: {test_dir}")
            print(f"  Annotation file: {ann_file}")
            print(f"  Image directory: {img_dir}")
            ds = get_coco_dataset(img_dir=str(img_dir), ann_file=str(ann_file))
            test_datasets.append(ds)
            print(f"  Loaded {len(ds)} samples")
        else:
            print(f"WARNING: Could not find dataset for {test_dir}")
    
    if not test_datasets:
        print("No test datasets found!")
        return
    
    test_ds = test_datasets[0] if len(test_datasets) == 1 else ConcatDataset(test_datasets)
    test_loader = DataLoader(
        test_ds, batch_size=4, shuffle=False, 
        collate_fn=lambda x: tuple(zip(*x))
    )
    
    print(f"\nTotal test samples: {len(test_ds)}")
    print(f"Test batches: {len(test_loader)}")
    
    # Full evaluation matrix
    print("\n" + "=" * 70)
    print("FULL EVALUATION MATRIX")
    print("=" * 70)
    print(f"{'IoU Threshold':<15} {'Score>0.3':<15} {'Score>0.5':<15} {'Score>0.7':<15}")
    print("-" * 70)
    
    for iou_thresh in [0.3, 0.5, 0.6, 0.75]:
        results = []
        for score_thresh in [0.3, 0.5, 0.7]:
            mAP = evaluate_mAP(
                model, test_loader, 
                iou_threshold=iou_thresh, 
                score_threshold=score_thresh
            )
            results.append(f"{mAP*100:.2f}%")
        print(f"{iou_thresh:<15} {results[0]:<15} {results[1]:<15} {results[2]:<15}")
    
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    # Count predictions at different score thresholds
    print("\nPrediction counts at different score thresholds:")
    model.eval()
    
    for score_thresh in [0.3, 0.5, 0.7, 0.9]:
        total_preds = 0
        total_gt = 0
        with torch.no_grad():
            for images, targets in test_loader:
                images = [img.to(device) for img in images]
                outputs = model(images)
                
                for output, target in zip(outputs, targets):
                    scores = output['scores']
                    preds_above_thresh = (scores >= score_thresh).sum().item()
                    total_preds += preds_above_thresh
                    total_gt += len(target)
        
        print(f"  score>{score_thresh}: {total_preds} predictions vs {total_gt} ground truth boxes")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test trained model on test dataset")
    parser.add_argument("--model", type=str, default="/home/livia/Desktop/model.pth",
                        help="Path to saved model weights")
    parser.add_argument("--iou", type=float, default=0.3,
                        help="IoU threshold for evaluation (default: 0.3)")
    
    args = parser.parse_args()
    
    test_saved_model(model_path=args.model, iou_threshold=args.iou)