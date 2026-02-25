import cv2
import numpy as np
import math
from pathlib import Path

# ----------------------------
# Config (edit if you want)
# ----------------------------
# Colors in BGR (OpenCV uses BGR, not RGB)
QUAD_COLORS = {
    "NE": (0, 255, 255),   # yellow
    "SE": (0, 255, 0),     # green
    "SW": (255, 0, 0),     # blue
    "NW": (255, 0, 255),   # magenta
}
THICKNESS = 4
CENTER_DOT_RADIUS = 5
# Default radius (pixels) used when a radius is not provided. Change as desired.
DEFAULT_RADIUS = 500

# ----------------------------
# Mouse click capture
# ----------------------------
clicks = []

def on_mouse(event, x, y, flags, param):
    global clicks
    if event == cv2.EVENT_LBUTTONDOWN:
        clicks.append((x, y))
        print(f"Click {len(clicks)}: ({x}, {y})")


def angle_deg_from_center_to_point(cx, cy, px, py):
    """
    Returns angle in degrees for OpenCV's arc system.
    OpenCV ellipse angles are in degrees, measured clockwise from the +x axis.
    Image y-axis points down, so atan2(dy, dx) can be used and converted.
    """
    dx = px - cx
    dy = py - cy
    ang = math.degrees(math.atan2(dy, dx))  # in [-180, 180]
    # Convert to [0, 360) and keep as clockwise-from-+x convention
    ang = ang % 360
    return ang


def draw_quadrant_arcs(frame, center, radius, north_angle_deg):
    """
    Draw 4 quadrant arcs (NE, SE, SW, NW) based on where North points.

    Quadrants are 90-degree wedges:
    - NE: North -> East
    - SE: East -> South
    - SW: South -> West
    - NW: West -> North
    """
    cx, cy = center
    r = int(round(radius))

    # North is a direction. Define East/South/West as +90/+180/+270 degrees clockwise.
    ang_N = north_angle_deg
    ang_E = ang_N + 90
    ang_S = ang_N + 180
    ang_W = ang_N + 270

    def norm(a):
        return a % 360

    ang_N = norm(ang_N)
    ang_E = norm(ang_E)
    ang_S = norm(ang_S)
    ang_W = norm(ang_W)

    # Helper: draw an arc from start to start+90 (clockwise)
    def draw_arc(start_deg, color):
        end_deg = (start_deg + 90) % 360
        # cv2.ellipse uses start/end angles in degrees. If end < start, split the arc.
        if end_deg > start_deg:
            cv2.ellipse(frame, (cx, cy), (r, r), 0, start_deg, end_deg, color, THICKNESS)
        else:
            cv2.ellipse(frame, (cx, cy), (r, r), 0, start_deg, 360, color, THICKNESS)
            cv2.ellipse(frame, (cx, cy), (r, r), 0, 0, end_deg, color, THICKNESS)

    # Define quadrants starting at North going clockwise:
    # NE: N -> E, SE: E -> S, SW: S -> W, NW: W -> N
    draw_arc(ang_N, QUAD_COLORS["NE"])
    draw_arc(ang_E, QUAD_COLORS["SE"])
    draw_arc(ang_S, QUAD_COLORS["SW"])
    draw_arc(ang_W, QUAD_COLORS["NW"])

    # Draw axis lines for N, E, S, W so the cardinal directions are explicit.
    axis_color = (255, 255, 255)
    axis_thickness = max(2, THICKNESS - 1)
    for ang in (ang_N, ang_E, ang_S, ang_W):
        rad = math.radians(ang)
        x = int(round(cx + 2 * r * math.cos(rad)))
        y = int(round(cy + 2 * r * math.sin(rad)))
        cv2.line(frame, (cx, cy), (x, y), axis_color, axis_thickness)

    # Mark center
    cv2.circle(frame, (cx, cy), CENTER_DOT_RADIUS, (255, 255, 255), -1)


def annotate_video(video_path: str, out_path: str, radius: float = None):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(out_path, fourcc, fps, (w, h))

    # Read first frame for calibration clicks
    ok, first = cap.read()
    if not ok:
        raise RuntimeError("Could not read first frame.")

    global clicks
    clicks = []

    show = first.copy()
    win_name = "Calibrate (click center, then north)"
    cv2.namedWindow(win_name)
    cv2.setMouseCallback(win_name, on_mouse)

    while True:
        temp = show.copy()
        # show clicked points as you go
        for i, (x, y) in enumerate(clicks):
            cv2.circle(temp, (x, y), 6, (0, 0, 255), -1)
            cv2.putText(temp, f"{i+1}", (x+8, y-8), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.imshow(win_name, temp)
        key = cv2.waitKey(20) & 0xFF

        if len(clicks) >= 2:
            break
        if key == 27:  # ESC
            cap.release()
            out.release()
            cv2.destroyAllWindows()
            return

    cv2.destroyAllWindows()

    (cx, cy), (nx, ny) = clicks[0], clicks[1]
    # Use provided radius (from CLI) if given, otherwise use the DEFAULT_RADIUS value.
    if radius is None:
        radius = DEFAULT_RADIUS
    north_angle = angle_deg_from_center_to_point(cx, cy, nx, ny)

    print(f"Center: ({cx},{cy}), North point: ({nx},{ny})")
    print(f"Radius: {radius:.2f} px, North angle: {north_angle:.2f} deg (OpenCV angle convention)")

    # Annotate first frame and write it
    frame0 = first.copy()
    draw_quadrant_arcs(frame0, (cx, cy), radius, north_angle)
    out.write(frame0)

    # Annotate the rest
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        draw_quadrant_arcs(frame, (cx, cy), radius, north_angle)
        out.write(frame)

    cap.release()
    out.release()
    print(f"Saved annotated video to: {out_path}")


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Annotate video with quadrant arcs around a center point.")
    parser.add_argument("video", nargs='?', default="/home/livia/AntTrack/ant_tracker/clip_10s.mp4",
                        help="Input video path")
    parser.add_argument("out", nargs='?', default="/home/livia/AntTrack/ant_tracker/10s_clip_ants_annotated.mp4",
                        help="Output video path")

    parser.add_argument("--center", nargs=2, type=int, metavar=("CX", "CY"),
                        help="Center coordinates (x y). If provided, skips interactive calibration.")
    parser.add_argument("--north", nargs=2, type=int, metavar=("NX", "NY"),
                        help="North point coordinates (x y). If provided together with --center, skips interactive calibration.")
    parser.add_argument("--radius", type=float, default=None,
                        help=f"Optional radius to use instead of computing from center and north point. If omitted, uses DEFAULT_RADIUS={DEFAULT_RADIUS} px.")

    args = parser.parse_args()

    # If no DISPLAY (headless), require non-interactive coords
    if os.environ.get("DISPLAY") is None and (args.center is None or args.north is None):
        raise RuntimeError("No DISPLAY detected. Provide --center and --north coordinates when running headless.")

    if args.center is not None and args.north is not None:
        cx, cy = args.center
        nx, ny = args.north
        # Use provided radius if given, otherwise use the DEFAULT_RADIUS constant.
        radius = args.radius if args.radius is not None else DEFAULT_RADIUS
        north_angle = angle_deg_from_center_to_point(cx, cy, nx, ny)

        # Open video and write annotated frames without interactive calibration
        cap = cv2.VideoCapture(args.video)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {args.video}")
        fps = cap.get(cv2.CAP_PROP_FPS)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(args.out, fourcc, fps, (w, h))

        # Annotate all frames
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            draw_quadrant_arcs(frame, (cx, cy), radius, north_angle)
            out.write(frame)

        cap.release()
        out.release()
        print(f"Saved annotated video to: {args.out}")
    else:
        # Interactive mode (GUI required) — pass through the optional radius argument
        annotate_video(args.video, args.out, args.radius)
