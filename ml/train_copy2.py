import torch
import torchvision
from torch.utils.data import DataLoader, random_split
from torchvision.models.detection import FasterRCNN
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.faster_rcnn import FasterRCNN_ResNet50_FPN_V2_Weights
from antsdataset import get_coco_dataset
from valid_updated import evaluate_mAP
from ray import tune
from ray.tune.search.optuna import OptunaSearch
from pathlib import Path
from torch.utils.data import ConcatDataset
import traceback


def get_model(num_classes):
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn_v2(
        weights=FasterRCNN_ResNet50_FPN_V2_Weights.DEFAULT
    )

    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
    return model


def load_data(
    test_dirs=None,
    exclude_test_from_train=True,
    train_val_ratio=8 / 9,
    batch_size=4,
):
    base_dir = Path(__file__).parent
    ann_candidates = list(base_dir.rglob("*annotations*.json"))

    datasets = []
    ds_sources = []
    if ann_candidates:
        for ann in ann_candidates:
            img_dir_candidate = ann.parent / "images"
            if img_dir_candidate.exists():
                img_dir = str(img_dir_candidate)
            else:
                img_dir = str(ann.parent)
            print(f"Loading dataset: ann_file={ann}, img_dir={img_dir}")
            try:
                ds = get_coco_dataset(img_dir=img_dir, ann_file=str(ann))
                datasets.append(ds)
                ds_sources.append(img_dir)
            except Exception as e:
                print(f"Warning: failed to load dataset from {ann}: {e}")

    if not datasets:
        print(
            "No annotation candidates found under ml/. Falling back to the default single dataset path."
        )
        total_dataset = get_coco_dataset(
            img_dir="/home/livia/Desktop/Seq0006Object21Image64/img",
            ann_file="/home/livia/Desktop/Seq0006Object21Image64/annotations.coco.json",
        )
        total_len = len(total_dataset)
        if total_len == 0:
            raise RuntimeError("Fallback dataset is empty.")
        test_size = max(1, int(0.1 * total_len))
        val_size = max(1, int(0.1 * total_len))
        train_size = total_len - val_size - test_size
        if train_size <= 0:
            train_size = max(1, total_len - val_size - test_size)
        train_ds, val_ds, test_ds = random_split(
            total_dataset, [train_size, val_size, test_size]
        )
    else:
        test_dirs = test_dirs or []
        test_datasets = []
        other_datasets = []
        for ds, src in zip(datasets, ds_sources):
            if any(td in src for td in test_dirs):
                test_datasets.append(ds)
            else:
                other_datasets.append(ds)

        if not exclude_test_from_train:
            other_datasets = other_datasets + test_datasets

        if other_datasets:
            total_other = (
                other_datasets[0]
                if len(other_datasets) == 1
                else ConcatDataset(other_datasets)
            )
        else:
            total_other = (
                datasets[0] if len(datasets) == 1 else ConcatDataset(datasets)
            )

        if test_datasets:
            test_ds = (
                test_datasets[0]
                if len(test_datasets) == 1
                else ConcatDataset(test_datasets)
            )
        else:
            test_ds = None

        total_len = len(total_other)
        if total_len == 0:
            raise RuntimeError("No samples available for train/val after splitting.")
        train_size = int(train_val_ratio * total_len)
        val_size = total_len - train_size
        if train_size == 0:
            train_size = max(1, total_len - 1)
            val_size = total_len - train_size

        train_ds, val_ds = random_split(total_other, [train_size, val_size])

    print(f"Dataset sizes: train={len(train_ds)}, val={len(val_ds)}, test={len(test_ds) if test_ds else 0}")

    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True, collate_fn=lambda x: tuple(zip(*x))
    )
    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False, collate_fn=lambda x: tuple(zip(*x))
    )
    test_loader = (
        DataLoader(test_ds, batch_size=batch_size, shuffle=False, collate_fn=lambda x: tuple(zip(*x)))
        if test_ds is not None
        else None
    )

    return train_loader, val_loader, test_loader


def test_data_loading():
    """
    Test function to verify all datasets are loaded correctly.
    Run this before training to ensure data is set up properly.
    """
    print("=" * 60)
    print("TESTING DATA LOADING")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    ann_candidates = list(base_dir.rglob("*annotations*.json"))
    
    print(f"\nFound {len(ann_candidates)} annotation files:")
    for i, ann in enumerate(ann_candidates):
        print(f"  {i+1}. {ann}")
    
    print("\n" + "-" * 60)
    print("Loading each dataset individually:")
    print("-" * 60)
    
    datasets_info = []
    for ann in ann_candidates:
        img_dir_candidate = ann.parent / "images"
        if img_dir_candidate.exists():
            img_dir = str(img_dir_candidate)
        else:
            img_dir = str(ann.parent)
        
        try:
            ds = get_coco_dataset(img_dir=img_dir, ann_file=str(ann))
            num_samples = len(ds)
            datasets_info.append({
                "ann_file": str(ann),
                "img_dir": img_dir,
                "num_samples": num_samples,
                "status": "OK"
            })
            print(f"  ✓ {ann.parent.name}: {num_samples} samples")
        except Exception as e:
            datasets_info.append({
                "ann_file": str(ann),
                "img_dir": img_dir,
                "num_samples": 0,
                "status": f"FAILED: {e}"
            })
            print(f"  ✗ {ann.parent.name}: FAILED - {e}")
    
    print("\n" + "-" * 60)
    print("Testing train/val/test split:")
    print("-" * 60)
    
    test_dirs = [
        "project-2-at-2026-03-13-18-47-03b7cba6",
        "project-3-at-2026-03-13-18-57-9ddf8827",
    ]
    
    print(f"\nTest directories (will be used for test set):")
    for td in test_dirs:
        print(f"  - {td}")
    
    try:
        train_loader, val_loader, test_loader = load_data(
            test_dirs=test_dirs, 
            exclude_test_from_train=True, 
            batch_size=4
        )
        
        print(f"\n✓ Data loading successful!")
        print(f"  Train batches: {len(train_loader)} (batch_size=4)")
        print(f"  Val batches: {len(val_loader)} (batch_size=4)")
        print(f"  Test batches: {len(test_loader) if test_loader else 0} (batch_size=4)")
        
        # Calculate approximate sample counts
        train_samples = len(train_loader) * 4
        val_samples = len(val_loader) * 4
        test_samples = len(test_loader) * 4 if test_loader else 0
        
        print(f"\n  Approximate sample counts:")
        print(f"    Train: ~{train_samples}")
        print(f"    Val: ~{val_samples}")
        print(f"    Test: ~{test_samples}")
        print(f"    Total: ~{train_samples + val_samples + test_samples}")
        
    except Exception as e:
        print(f"\n✗ Data loading FAILED: {e}")
        traceback.print_exc()
        return False
    
    print("\n" + "-" * 60)
    print("Testing sample batch loading:")
    print("-" * 60)
    
    try:
        # Test loading one batch from each loader
        print("\n  Loading one batch from train_loader...")
        images, targets = next(iter(train_loader))
        print(f"    ✓ Got {len(images)} images")
        print(f"    ✓ First image shape: {images[0].shape}")
        print(f"    ✓ First target has {len(targets[0])} annotations")
        
        print("\n  Loading one batch from val_loader...")
        images, targets = next(iter(val_loader))
        print(f"    ✓ Got {len(images)} images")
        
        if test_loader:
            print("\n  Loading one batch from test_loader...")
            images, targets = next(iter(test_loader))
            print(f"    ✓ Got {len(images)} images")
        
    except Exception as e:
        print(f"\n  ✗ Batch loading FAILED: {e}")
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    
    return True


def objective(config):
    try:
        device = torch.device('cuda')
        test_dirs = [
            "project-2-at-2026-03-13-18-47-03b7cba6",
            "project-3-at-2026-03-13-18-57-9ddf8827",
        ]
        train_loader, val_loader, test_loader = load_data(
            test_dirs=test_dirs, exclude_test_from_train=True, batch_size=4
        )

        num_classes = 2
        model = get_model(num_classes)
        model.to(device)

        optimizer = torch.optim.SGD(
            model.parameters(),
            lr=config["lr"],
            momentum=config["momentum"],
            weight_decay=config["weight_decay"],
        )

        epoch = 0
        while True:
            print(f"Starting epoch {epoch}")
            train_one_epoch(model, optimizer, train_loader, device)
            model_path = f"/home/livia/Desktop/model.pth"
            torch.save(model.state_dict(), model_path)
            print(f"Model saved: {model_path}")

            try:
                val_acc = evaluate_mAP(model, val_loader, iou_threshold=0.6, score_threshold=0.5)
                if val_acc is None:
                    print(f"Warning: evaluate_mAP returned None, using 0.0")
                    val_acc = 0.0
                elif isinstance(val_acc, float) and (val_acc != val_acc):
                    print(f"Warning: evaluate_mAP returned NaN, using 0.0")
                    val_acc = 0.0
            except Exception as e:
                print(f"Warning: evaluate_mAP failed: {e}")
                traceback.print_exc()
                val_acc = 0.0

            print(f"Epoch {epoch} val_AP@0.6: {val_acc}")

            metrics = {"val_AP": float(val_acc)}

            if test_loader is not None:
                try:
                    test_acc = evaluate_mAP(model, test_loader, iou_threshold=0.6, score_threshold=0.5)
                    if test_acc is not None and test_acc == test_acc:
                        metrics["test_AP"] = float(test_acc)
                        print(f"Epoch {epoch} test_AP@0.6: {test_acc}")
                except Exception as e:
                    print(f"Warning: test evaluation failed: {e}")

            # Use tune.report with dictionary unpacking
            tune.report(val_AP=metrics["val_AP"], **{k: v for k, v in metrics.items() if k != "val_AP"})
            epoch += 1

    except Exception as e:
        print(f"ERROR in objective: {e}")
        traceback.print_exc()
        raise


def train_one_epoch(model, optimizer, data_loader, device):
    model.train()
    batch_idx = 0
    for images, targets in data_loader:
        try:
            images = [img.to(device) for img in images]

            processed_targets = []
            valid_images = []
            for i, target in enumerate(targets):
                boxes = []
                labels = []
                for obj in target:
                    bbox = obj["bbox"]
                    x, y, w, h = bbox

                    if w > 0 and h > 0:
                        boxes.append([x, y, x + w, y + h])
                        labels.append(obj["category_id"])

                if boxes:
                    processed_target = {
                        "boxes": torch.tensor(boxes, dtype=torch.float32).to(device),
                        "labels": torch.tensor(labels, dtype=torch.int64).to(device),
                    }
                    processed_targets.append(processed_target)
                    valid_images.append(images[i])

            if not processed_targets:
                continue

            images = valid_images

            loss_dict = model(images, processed_targets)
            losses = sum(loss for loss in loss_dict.values())

            optimizer.zero_grad()
            losses.backward()
            optimizer.step()

            if batch_idx % 50 == 0:
                print(f"  Batch {batch_idx}, loss={losses.item():.4f}")
            batch_idx += 1

        except Exception as e:
            print(f"ERROR in train_one_epoch batch {batch_idx}: {e}")
            traceback.print_exc()
            raise


if __name__ == "__main__":
    import sys
    
    # If run with --test flag, only test data loading
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = test_data_loading()
        sys.exit(0 if success else 1)
    
    # Normal training
    search_space = {
        "lr": tune.loguniform(1e-5, 1e-1),
        "momentum": tune.uniform(0.0, 0.99),
        "weight_decay": tune.loguniform(1e-6, 1e-2),
    }
    algo = OptunaSearch()

    objective_with_resources = tune.with_resources(objective, {"gpu": 1})

    tuner = tune.Tuner(
        objective_with_resources,
        tune_config=tune.TuneConfig(
            metric="val_AP",
            mode="max",
            search_alg=algo,
            num_samples=10,
        ),
        run_config=tune.RunConfig(
            stop={"training_iteration": 5},
            verbose=2,
        ),
        param_space=search_space,
    )
    results = tuner.fit()

    try:
        best_result = results.get_best_result(metric="val_AP", mode="max", filter_nan_and_inf=False)
        print("Best config is:", best_result.config)
        print("Best val_AP@0.6:", best_result.metrics.get("val_AP"))
    except RuntimeError as e:
        print(f"Could not get best result: {e}")
        print("All results:")
        for result in results:
            print(f"  Config: {result.config}, Metrics: {result.metrics}")