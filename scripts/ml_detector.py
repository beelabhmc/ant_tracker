import os

from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np
import torch
import torchvision
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
    score_thresh: float = 0.5
    ant_class_id: int = 1  # background=0, ant=1
    num_classes: int = 2


class MLDetector:
    """
    Drop-in replacement for `scripts/detector.py::Detector` that returns:
      - centers: list[np.ndarray] where each element has shape (2, 1) => [[x],[y]]
      - areas: list[float]
    """

    def __init__(self, config: MLDetectorConfig):
        self.config = config
        self.device = torch.device(config.device)

        model = _build_fasterrcnn_resnet50_fpn_v2(num_classes=config.num_classes)
        state = torch.load(config.weights_path, map_location="cuda" if self.device.type == "cuda" else "cpu")
        model.load_state_dict(state)
        model.to(self.device)
        model.eval()
        self.model = model

        # TorchVision weights include recommended preprocessing metadata.
        self._weights = FasterRCNN_ResNet50_FPN_V2_Weights.DEFAULT

    @torch.inference_mode()
    def Detect(self, frame_bgr: np.ndarray) -> Tuple[List[np.ndarray], List[float]]:
        # frame comes from OpenCV (BGR uint8). Convert to RGB for TorchVision.
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        # Convert to float tensor in [0, 1], CHW.
        img = torch.from_numpy(frame_rgb).to(torch.float32) / 255.0
        img = img.permute(2, 0, 1)

        # Match TorchVision's expected normalization for this backbone.
        preprocess = self._weights.transforms()
        img = preprocess(img)
        img = img.to(self.device)

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

        centers: List[np.ndarray] = []
        areas: List[float] = []

        for (x1, y1, x2, y2), score, label in zip(boxes, scores, labels):
            if int(label) != int(self.config.ant_class_id):
                continue
            if float(score) < float(self.config.score_thresh):
                continue

            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            w = max(0.0, x2 - x1)
            h = max(0.0, y2 - y1)
            area = float(w * h)

            centers.append(np.round(np.array([[cx], [cy]])))
            areas.append(area)

        return centers, areas

