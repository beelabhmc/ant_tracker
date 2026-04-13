import argparse
import os

import constants
from track_one_clip_new import make_history_CSV, make_merge_vids, trackOneClip


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "source",
        type=str,
        help="The path to a video file in which we want to track the ants.",
    )
    arg_parser.add_argument(
        "history_path",
        type=str,
        help="The path to a directory in which to save the history csv.",
    )
    arg_parser.add_argument(
        "video_path",
        type=str,
        nargs="?",
        default=None,
        help="The path to a directory in which to dump annotated result videos. "
        "If no path is given, then it does not export videos.",
    )

    # Tracking params (same defaults as legacy script)
    arg_parser.add_argument(
        "-it",
        "--invisible-threshold",
        dest="invisible_threshold",
        type=int,
        default=constants.INVISIBLE_FOR_TOO_LONG,
        help="The number of frames after which to forget a new, missing track.",
    )
    arg_parser.add_argument(
        "-tdt",
        "--tracker-distance-threshold",
        dest="tracker_distance_threshold",
        type=int,
        default=constants.TRACKER_DISTANCE_THRESHOLD,
        help="The distance threshold. When the threshold is exceeded, the track will be deleted and a new track will be created",
    )
    arg_parser.add_argument(
        "-ttl",
        "--tracker-trace-length",
        dest="tracker_trace_length",
        type=int,
        default=constants.TRACKER_TRACE_LENGTH,
        help="Trace path history length (good for debugging purposes)",
    )
    arg_parser.add_argument(
        "-nac",
        "--no-ant-counter-frames-total",
        dest="no_ant_counter_frames_total",
        type=int,
        default=constants.NO_ANT_COUNTER_FRAMES_TOTAL,
        help="If the ant is not detected for N frames, we can safely assume it has left the track",
    )
    arg_parser.add_argument(
        "-eb",
        "--edge-border",
        dest="edge_border",
        type=int,
        default=constants.EDGE_BORDER,
        help="Creates a border around the ROI. If the ant disappears within the border, we can assume it has left an edge.",
    )
    arg_parser.add_argument(
        "-md",
        "--merge-distance",
        dest="merge_distance",
        type=int,
        default=constants.MERGE_DISTANCE,
        help="The maximum distance allowed between two existing tracks for it to be considered a merger.",
    )

    # ML detector params (required)
    arg_parser.add_argument(
        "--model-weights",
        dest="model_weights_path",
        type=str,
        required=True,
        help="Path to Faster R-CNN .pth weights (state_dict).",
    )
    arg_parser.add_argument(
        "--model-device",
        dest="model_device",
        type=str,
        default="cuda",
        help="Device for ML detector: 'cpu', 'cuda', or 'mps'.",
    )
    arg_parser.add_argument(
        "--model-score-thresh",
        dest="model_score_thresh",
        type=float,
        default=0.75,
        help="Confidence threshold for kept boxes (default 0.75). Raise if you get too many false tracks.",
    )
    arg_parser.add_argument(
        "--model-nms-iou",
        dest="model_nms_iou",
        type=float,
        default=0.45,
        help="Extra NMS IoU threshold on CPU after inference (default 0.45). Use -1 to disable.",
    )
    arg_parser.add_argument(
        "--model-max-detections",
        dest="model_max_detections",
        type=int,
        default=32,
        help="Max boxes per frame after NMS (default 32). Use 0 for no limit.",
    )
    arg_parser.add_argument(
        "--model-min-box-area",
        dest="model_min_box_area",
        type=int,
        default=None,
        help="Drop detections with box area smaller than this (pixels^2).",
    )
    arg_parser.add_argument(
        "--model-max-box-area",
        dest="model_max_box_area",
        type=int,
        default=None,
        help="Drop detections with box area larger than this (pixels^2).",
    )
    arg_parser.add_argument(
        "--model-motion-gate",
        dest="model_motion_gate",
        action="store_true",
        default=True,
        help="Enable previous-frame motion gating (default on; good for fixed cameras).",
    )
    arg_parser.add_argument(
        "--no-model-motion-gate",
        dest="model_motion_gate",
        action="store_false",
        help="Disable motion gating.",
    )
    arg_parser.add_argument(
        "--model-motion-pixel-thresh",
        dest="model_motion_pixel_thresh",
        type=int,
        default=18,
        help="Pixel absdiff threshold for motion gating (0-255, default 18).",
    )
    arg_parser.add_argument(
        "--model-motion-min-fraction",
        dest="model_motion_min_fraction",
        type=float,
        default=0.02,
        help="Min fraction of changed pixels inside a box (default 0.02).",
    )

    args = arg_parser.parse_args()

    model_nms_iou = None if args.model_nms_iou < 0 else args.model_nms_iou
    model_max_detections = None if args.model_max_detections == 0 else args.model_max_detections

    print("Tracking ants in", args.source)
    export = args.video_path is not None

    if args.video_path is None:
        args.video_path = ""

    tracker_object = trackOneClip(
        args.source,
        args.video_path,
        export,
        args.tracker_distance_threshold,
        args.tracker_trace_length,
        args.no_ant_counter_frames_total,
        args.edge_border,
        args.merge_distance,
        model_weights_path=args.model_weights_path,
        model_device=args.model_device,
        model_score_thresh=args.model_score_thresh,
        model_nms_iou=model_nms_iou,
        model_max_detections=model_max_detections,
        model_min_box_area=args.model_min_box_area,
        model_max_box_area=args.model_max_box_area,
        model_motion_gate=args.model_motion_gate,
        model_motion_pixel_thresh=args.model_motion_pixel_thresh,
        model_motion_min_fraction=args.model_motion_min_fraction,
    )

    # makes the history csvs
    final_result_path_history = make_history_CSV(tracker_object, args.history_path)

    # this makes the intermediate directories "merger" and "merger_annotated"
    roi = os.path.splitext(os.path.basename(args.history_path))[0]
    split = os.path.dirname(args.history_path)
    video = os.path.dirname(split)
    intermediate = os.path.dirname(os.path.dirname(video))

    split = split.split("/")[-1]
    video = video.split("/")[-1]

    merger_dir = os.path.join(os.path.join(os.path.join(os.path.join(intermediate, "merger"), video), split), roi)
    merger_annotated_dir = os.path.join(
        os.path.join(os.path.join(os.path.join(intermediate, "merger_annotated"), video), split), roi
    )

    # makes the merge videos
    make_merge_vids(final_result_path_history, args.source, args.video_path, merger_dir, merger_annotated_dir)


if __name__ == "__main__":
    main()

