import torch
from pathlib import Path
from torch.utils.data import DataLoader, ConcatDataset
import sys
sys.path.append(str(Path(__file__).parent))

from train_copy2 import get_model
from antsdataset import get_coco_dataset


def debug_evaluation(model_path="/home/livia/Desktop/model_updated.pth"):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Load model
    num_classes = 2
    model = get_model(num_classes)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    
    print(f"Loaded model from: {model_path}")
    
    # Load test dataset
    test_dir = "project-3-at-2026-03-13-18-57-9ddf8827"
    base_dir = Path(__file__).parent
    
    matches = list(base_dir.rglob(f"*{test_dir}*/*annotations*.json"))
    if matches:
        ann_file = matches[0]
        img_dir = ann_file.parent / "images"
        if not img_dir.exists():
            img_dir = ann_file.parent
        
        print(f"Loading test dataset: {test_dir}")
        ds = get_coco_dataset(img_dir=str(img_dir), ann_file=str(ann_file))
        print(f"Loaded {len(ds)} samples")
    else:
        print("Dataset not found!")
        return
    
    test_loader = DataLoader(
        ds, batch_size=1, shuffle=False, 
        collate_fn=lambda x: tuple(zip(*x))
    )
    
    print("\n" + "=" * 70)
    print("DETAILED PREDICTION ANALYSIS")
    print("=" * 70)
    
    total_gt = 0
    total_preds_03 = 0
    total_preds_05 = 0
    total_preds_07 = 0
    
    with torch.no_grad():
        for batch_idx, (images, targets) in enumerate(test_loader):
            images = [img.to(device) for img in images]
            outputs = model(images)
            
            for img_idx, (output, target) in enumerate(zip(outputs, targets)):
                boxes = output['boxes'].cpu().numpy()
                scores = output['scores'].cpu().numpy()
                labels = output['labels'].cpu().numpy()
                
                gt_count = len(target)
                total_gt += gt_count
                
                preds_03 = (scores >= 0.3).sum()
                preds_05 = (scores >= 0.5).sum()
                preds_07 = (scores >= 0.7).sum()
                
                total_preds_03 += preds_03
                total_preds_05 += preds_05
                total_preds_07 += preds_07
                
                print(f"\nImage {batch_idx}:")
                print(f"  Ground truth boxes: {gt_count}")
                print(f"  Total predictions: {len(scores)}")
                print(f"  Predictions score>0.3: {preds_03}")
                print(f"  Predictions score>0.5: {preds_05}")
                print(f"  Predictions score>0.7: {preds_07}")
                
                if len(scores) > 0:
                    print(f"  Score range: [{scores.min():.4f}, {scores.max():.4f}]")
                    print(f"  Top 5 scores: {sorted(scores, reverse=True)[:5]}")
                
                # Show ground truth details
                if gt_count > 0:
                    print(f"  Ground truth annotations:")
                    for i, t in enumerate(target):
                        print(f"    {i+1}. bbox={t['bbox']}, category={t['category_id']}")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total ground truth boxes: {total_gt}")
    print(f"Total predictions score>0.3: {total_preds_03}")
    print(f"Total predictions score>0.5: {total_preds_05}")
    print(f"Total predictions score>0.7: {total_preds_07}")
    
    # Now let's check what evaluate_mAP actually does
    print("\n" + "=" * 70)
    print("CHECKING evaluate_mAP FUNCTION")
    print("=" * 70)
    
    from valid_updated import evaluate_mAP
    
    # Check source code of evaluate_mAP
    import inspect
    print("\nevaluate_mAP source code:")
    print("-" * 70)
    try:
        source = inspect.getsource(evaluate_mAP)
        print(source[:2000])  # First 2000 chars
    except:
        print("Could not get source code")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="/home/livia/Desktop/model_updated.pth")
    args = parser.parse_args()
    
    debug_evaluation(model_path=args.model)