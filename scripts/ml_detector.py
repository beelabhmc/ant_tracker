import os

from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np
import torch
import torchvision
import torchvision.ops
from torchvision.transforms import functional as F
from torchvision.models.detection.faster_rcnn import (
    FastRCNNPredictor,
    FasterRCNN_ResNet50_FPN_V2_Weights,
)


def _build_fasterrcnn_resnet50_fpn_v2(num_classes: int) -> torch.nn.Module:
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn_v2(
        weights=FasterRCNN_ResNet50_FPN_V2_Weights.DEFAULT
    )
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
    return model


@dataclass(frozen=True)
class MLDetectorConfig:
    weights_path: str
    device: str = "cuda"  # "cpu", "cuda", "mps"
    score_thresh: float = 0.75
    ant_class_id: int = 1  # TorchVision Faster R-CNN: 0=background, 1=first object class
    num_classes: int = 2
    # Extra post-processing — the tracker expects a small, clean set of points per frame.
    # Without this, a noisy model can emit hundreds of boxes and break Hungarian matching.
    nms_iou: Optional[float] = 0.45
    max_detections: Optional[int] = 32  # keep highest-scoring boxes after NMS; None = no cap
    min_box_area: Optional[float] = None  # pixels^2; drop tiny false positives
    max_box_area: Optional[float] = None  # pixels^2; drop huge spurious boxes
    # Motion gating (fixed-camera friendly). Uses previous-frame absdiff on grayscale.
    # Keeps a box only if enough pixels changed inside it.
    motion_gate: bool = True
    motion_pixel_thresh: int = 18  # per-pixel absdiff threshold (0-255)
    motion_min_fraction: float = 0.02  # fraction of pixels above threshold required


class MLDetector:
    """
    Drop-in replacement for `scripts/detector.py::Detector` that returns:
      - centers: list[np.ndarray] where each element has shape (2, 1) => [[x],[y]]
      - areas: list[float]
    """

    def __init__(self, config: MLDetectorConfig):
        self.config = config
        self.device = torch.device(config.device)
        self._prev_gray: Optional[np.ndarray] = None

        model = _build_fasterrcnn_resnet50_fpn_v2(num_classes=config.num_classes)
        state = torch.load(config.weights_path, map_location="cuda" if self.device.type == "cuda" else "cpu")
        model.load_state_dict(state)
        model.to(self.device)
        model.eval()
        self.model = model

    @torch.inference_mode()
    def Detect(self, frame_bgr: np.ndarray) -> Tuple[List[np.ndarray], List[float]]:
        # IMPORTANT: match training preprocessing in `ml/antsdataset.py` and `ml/test.py`.
        # Those use `F.to_tensor` only (no additional normalization).
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        img = F.to_tensor(frame_rgb).to(self.device)

        outputs = self.model([img])
        out = outputs[0]

        boxes = out.get("boxes")
        scores = out.get("scores")
        labels = out.get("labels")

        if boxes is None or scores is None or labels is None:
            return [], []

        boxes = boxes.detach().to("cpu").numpy()
        scores = scores.detach().to("cpu").numpy()
        labels = labels.detach().to("cpu").numpy()

        mask = (labels == int(self.config.ant_class_id)) & (
            scores >= float(self.config.score_thresh)
        )
        boxes = boxes[mask]
        scores = scores[mask]
        if len(boxes) == 0:
            return [], []

        w = np.maximum(0.0, boxes[:, 2] - boxes[:, 0])
        h = np.maximum(0.0, boxes[:, 3] - boxes[:, 1])
        box_areas = w * h
        keep = np.ones(len(boxes), dtype=bool)
        if self.config.min_box_area is not None:
            keep &= box_areas >= float(self.config.min_box_area)
        if self.config.max_box_area is not None:
            keep &= box_areas <= float(self.config.max_box_area)
        boxes = boxes[keep]
        scores = scores[keep]
        box_areas = box_areas[keep]
        if len(boxes) == 0:
            return [], []

        if self.config.nms_iou is not None and len(boxes) > 1:
            boxes_t = torch.as_tensor(boxes, dtype=torch.float32)
            scores_t = torch.as_tensor(scores, dtype=torch.float32)
            idx = torchvision.ops.nms(boxes_t, scores_t, float(self.config.nms_iou))
            idx = idx.cpu().numpy()
            boxes = boxes[idx]
            scores = scores[idx]
            box_areas = box_areas[idx]

        if self.config.motion_gate:
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            if self._prev_gray is not None and self._prev_gray.shape == gray.shape:
                diff = cv2.absdiff(gray, self._prev_gray)
                keep = []
                h_img, w_img = gray.shape[:2]
                for (x1, y1, x2, y2) in boxes:
                    x1i = int(max(0, min(w_img - 1, np.floor(x1))))
                    x2i = int(max(0, min(w_img, np.ceil(x2))))
                    y1i = int(max(0, min(h_img - 1, np.floor(y1))))
                    y2i = int(max(0, min(h_img, np.ceil(y2))))
                    if x2i <= x1i or y2i <= y1i:
                        keep.append(False)
                        continue
                    roi = diff[y1i:y2i, x1i:x2i]
                    changed = (roi >= int(self.config.motion_pixel_thresh)).mean()
                    keep.append(changed >= float(self.config.motion_min_fraction))
                keep = np.asarray(keep, dtype=bool)
                boxes = boxes[keep]
                scores = scores[keep]
                box_areas = box_areas[keep]
            self._prev_gray = gray

            if len(boxes) == 0:
                return [], []

        if self.config.max_detections is not None and len(boxes) > int(
            self.config.max_detections
        ):
            order = np.argsort(-scores)[: int(self.config.max_detections)]
            boxes = boxes[order]
            scores = scores[order]
            box_areas = box_areas[order]

        centers: List[np.ndarray] = []
        areas: List[float] = []
        for (x1, y1, x2, y2), area in zip(boxes, box_areas):
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            centers.append(np.round(np.array([[cx], [cy]])))
            areas.append(float(area))

        return centers, areas

