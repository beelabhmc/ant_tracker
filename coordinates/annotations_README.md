# annotations.py README

## Overview

`annotations.py` is a Python script designed to annotate videos with quadrant arcs around a specified center point. The script uses OpenCV to draw colored arcs representing North-East (NE), South-East (SE), South-West (SW), and North-West (NW) quadrants, along with cardinal direction lines and a center marker.

## Features

- **Interactive Calibration**: Click on the video to specify the center point and north direction.
- **Non-Interactive Mode**: Provide coordinates via command-line arguments for headless environments.
- **Customizable Radius**: Set a custom radius for the quadrant arcs or use the default.
- **Quadrant Visualization**: Draws 90-degree arcs in different colors for each quadrant.
- **Cardinal Directions**: Includes axis lines for North, East, South, and West.
- **Center Marker**: Places a white dot at the specified center.

## Requirements

- Python 3.x
- OpenCV (cv2)
- NumPy
- pathlib (included in Python 3.4+)

Install dependencies using:
```bash
pip install opencv-python numpy
```

## Usage

### Interactive Mode (Requires GUI)

Run the script with input and output video paths. The script will display the first frame and prompt you to click twice: first on the center point, then on a point indicating north.

```bash
python annotations.py input_video.mp4 output_video.mp4
```

Optional: Specify a custom radius.

```bash
python annotations.py input_video.mp4 output_video.mp4 --radius 600
```

### Non-Interactive Mode (Headless)

Provide center and north coordinates via command-line arguments. Useful for automation or headless environments.

```bash
python annotations.py input_video.mp4 output_video.mp4 --center 500 300 --north 500 100 --radius 400
```

## Command-Line Arguments

- `video`: Input video file path (default: "/input/file/path.mp4")
- `out`: Output video file path (default: "/output/file/path.mp4")
- `--center CX CY`: Center coordinates (x y). Skips interactive calibration if provided with --north.
- `--north NX NY`: North point coordinates (x y). Skips interactive calibration if provided with --center.
- `--radius RADIUS`: Radius in pixels for the quadrant arcs (default: 500)

## Configuration

Edit the constants at the top of the script to customize:

- `QUAD_COLORS`: Colors for each quadrant (BGR format)
- `THICKNESS`: Line thickness for arcs
- `CENTER_DOT_RADIUS`: Radius of the center dot
- `DEFAULT_RADIUS`: Default radius when not specified

## Output

The script produces an annotated MP4 video with quadrant arcs overlaid on each frame. The annotations include:

- Colored arcs for each quadrant
- White axis lines for cardinal directions
- White center dot

## Notes

- In headless environments (no DISPLAY), you must provide --center and --north coordinates.
- The north angle is calculated using OpenCV's clockwise-from-positive-x convention.
- The script assumes the input video is in a format readable by OpenCV.

## Example

To annotate a video with center at (400, 300) and north at (400, 200):

```bash
python annotations.py my_video.mp4 annotated_video.mp4 --center 400 300 --north 400 200
```
