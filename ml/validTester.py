from valid import calculate_mAP
import unittest
from collections import defaultdict
import numpy as np

class TestMeanAveragePrecision(unittest.TestCase):
    # predictions: defaultdict- image_id: {[x1,y1,x2,y2,score],....}
    # ground truth: defaultdict- image_id: {[x1,y1,x2,y2],....}
    def setUp(self):
        self.t1_preds = defaultdict(list)
        self.t1_preds[0] = [np.array([
            [0.4, 0.1, 0.7, 0.3, 0.9],  # from [.55, .2, .3, .2, .9]
            [0.2, 0.5, 0.5, 0.7, 0.8],  # from [.35, .6, .3, .2, .8]
            [0.7, 0.6, 0.9, 0.8, 0.7]   # from [.8, .7, .2, .2, .7]
        ], dtype=np.float32)]

        self.t1_targets = defaultdict(list)
        self.t1_targets[0].append([0.4, 0.1, 0.7, 0.3, 0.9])
        self.t1_targets[0].append([0.2, 0.5, 0.5, 0.7, 0.8])
        self.t1_targets[0].append([0.7, 0.6, 0.9, 0.8, 0.7])
        
        self.t1_correct_mAP = 1

        self.t2_preds = defaultdict(list)
        self.t2_preds[1] = [np.array([
            [0.4, 0.1, 0.7, 0.3, 0.9]
        ], dtype=np.float32)]
        self.t2_preds[0] = [np.array([
            [0.2, 0.5, 0.5, 0.7, 0.8],
            [0.7, 0.6, 0.9, 0.8, 0.7]
        ], dtype=np.float32)]

        self.t2_targets = defaultdict(list)
        self.t2_targets[1].append([0.4, 0.1, 0.7, 0.3, 0.9])
        self.t2_targets[0].append([0.2, 0.5, 0.5, 0.7, 0.8])
        self.t2_targets[0].append([0.7, 0.6, 0.9, 0.8, 0.7])
        
        self.t2_correct_mAP = 1

        self.t3_preds = defaultdict(list)
        self.t3_preds[0] = [np.array([
            [0.05, 0.05, 0.15, 0.15, 0.9],
            [0.25, 0.25, 0.35, 0.35, 0.8],
            [0.45, 0.45, 0.55, 0.55, 0.7]
        ], dtype=np.float32)]

        self.t3_targets = defaultdict(list)
        self.t3_targets[0] = [
            [0.65, 0.05, 0.75, 0.15, 0.9],
            [0.85, 0.25, 0.95, 0.35, 0.8],
            [0.85, 0.65, 0.95, 0.75, 0.7]
        ]
        
        self.t3_correct_mAP = 0

        self.t4_preds = defaultdict(list)
        self.t4_preds[0] = [np.array([
            [0.1, 0.2, 0.2, 0.3, 0.9],
            [0.2, 0.5, 0.5, 0.7, 0.8],
            [0.7, 0.6, 0.9, 0.8, 0.7],
            [0.1, 0.1, 0.2, 0.2, 0.85],
            [0.8, 0.1, 0.9, 0.2, 0.80]
        ], dtype=np.float32)]

        self.t4_targets = defaultdict(list)
        self.t4_targets[0].append([0.4, 0.1, 0.7, 0.3, 0.9])
        self.t4_targets[0].append([0.2, 0.5, 0.5, 0.7, 0.8])
        self.t4_targets[0].append([0.7, 0.6, 0.9, 0.8, 0.7])
        self.t4_targets[0].append([0.1, 0.1, 0.2, 0.2, 0.6])
        self.t4_targets[0].append([0.8, 0.1, 0.9, 0.2, 0.75])
        
        self.t4_correct_mAP = 7 / 10

        self.epsilon = 1e-4

    def test_all_correct_one_class(self):
        ap = calculate_mAP(
            self.t1_preds,
            self.t1_targets,
            iou_threshold=.5
        )
        # print("All correct: ", ap)
        # print("tp: ", tp)
        # print("fp: ", fp)
        self.assertTrue(
            abs(self.t1_correct_mAP - ap) < self.epsilon)

    def test_all_correct_batch(self):
        ap = calculate_mAP(
            self.t2_preds,
            self.t2_targets,
            iou_threshold=.5
        )
        self.assertTrue(
            abs(self.t2_correct_mAP - ap) < self.epsilon)

    def test_all_wrong_boxes(self):
        ap = calculate_mAP(
            self.t3_preds,
            self.t3_targets,
            iou_threshold=.5
        )
        # print("All wrong box: ", ap)
        # print("tp: ", tp)
        # print("fp: ", fp)
        self.assertTrue(
            abs(self.t3_correct_mAP - ap) < self.epsilon)

    def test_one_inaccurate_box(self):
       ap = calculate_mAP(
            self.t4_preds,
            self.t4_targets,
            iou_threshold=.5
        )
       print(ap)
       self.assertTrue(
           abs(self.t4_correct_mAP - ap) < self.epsilon)


if __name__ == '__main__':
    print('Running Mean Average Precisions Tests:')
    unittest.main()