import cv2
in_path = "/home/livia/AntTrack/ant_tracker/GX0100280912colony57.MP4"
out_path = "/home/livia/AntTrack/ant_tracker/clip_60s.mp4"
duration_sec = 60

cap = cv2.VideoCapture(in_path)
fps = cap.get(cv2.CAP_PROP_FPS) or 30
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

frame_count = int(duration_sec * fps)
i = 0
while i < frame_count:
    ret, frame = cap.read()
    if not ret:
        break
    out.write(frame)
    i += 1

cap.release()
out.release()
print("Saved", out_path)
