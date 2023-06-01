import cv2
from detector import Detector, display
from tracker import Tracker
import collections
import csv
import os



def trackOneClip(
        vidPath, vidExport, video_path, result_path, minBlob, count_warning_threshold,
        num_gaussians, num_training_frames, minimum_background_ratio,
        cost_of_nonassignment, invisible_threshold, old_age_threshold,
        visibility_threshold, kalman_initial_error, kalman_motion_noise,
        kalman_measurement_noise, min_visible_count, min_duration, debug):
    
    #### Delete me!

    print("the vidPath is", vidPath)
    print("the video_path is", video_path)
    print("the result_path is", result_path)
    print("the vidExport is", vidExport)
    # print("the raw_results is", raw_re)

    cap = cv2.VideoCapture(vidPath)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    size = (width, height)
    # print(f"Resolution: {width}x{height}")

    detector = Detector(minBlob, num_gaussians)  # detector object
    tracker = Tracker(10, invisible_threshold, 10, 0)  # tracker object

    first_coord = False
    last_coord = False
    no_ant_counter_frames = 0

    track_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
                    (0, 255, 255), (255, 0, 255), (255, 127, 255),
                    (127, 0, 255), (127, 0, 127)]
    pause = False
    history = []
    seconds = 0.00

    filename, ant_id, x0, y0, t0, x1, y1, t1, number_warning, broken_track = [], \
        [], [], [], [], [], [], [], [], []

    # get relative path of vidPath
    start = os.path.abspath(__file__)
    relative_path = os.path.relpath(vidPath, start)

    # displayed Track ID
    displayTrackID = tracker.getTrackID() + 1  # automatically increment by one

    if vidExport:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for MP4 video
        # fourcc = cv2.VideoWriter_fourcc(*'H264')  # H264 codec
        video_writer = cv2.VideoWriter(video_path, fourcc, fps, size)

    while (True):
        ret, frame = cap.read()  # read frame
        if not ret:
            break  # done with vidPath

        # detect ants
        centers = detector.Detect(frame)

        # Prints and stores where ant was last seen
        if no_ant_counter_frames > 10 and not last_coord and len(history) > 0:
            try:
                # print(f"Ant was last seen on coordinates {history[-1]} at time {seconds}")

                x1.append(history[-1][0])
                y1.append(history[-1][1])
                t1.append(seconds)

                history = []
            except:
                pass

            first_coord = False
            last_coord = True

            # update and display new trackID
            tracker.incrementID()
            displayTrackID = tracker.getTrackID()

        # for when ants are detected
        if len(centers) > 0:
            # threshold for too many ants  # should be 10
            if len(centers) > count_warning_threshold:
                print("There are a lot of ants")


            tracker.Update(centers)  # track using Kalman

            # store ant location (past 10 frames) into memory
            for ant in centers:
                history.append((int(ant[0][0]), int(ant[1][0])))
                if len(history) > 10:
                    history = history[1:]
            no_ant_counter_frames = 0

            # get timestamp and display
            timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
            seconds = round(timestamp / 1000, 2)
            timestamp_text = f"{seconds}"
            if debug or vidExport:
                cv2.putText(frame, timestamp_text, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 255, 0), 2)

            # displays and stores where ant was first seen (for multiple ants, use for)
            # also stores filename, timestamp, id, etc.
            if not first_coord:
                # print(
                #     f"Ant was first seen on coordinates ({int(ant[0][0])}, {int(ant[1][0])}) at time {seconds}")
                first_coord = True
                last_coord = False

                filename.append(relative_path)
                ant_id.append(tracker.getTrackID())
                x0.append(int(ant[0][0]))
                y0.append(int(ant[1][0]))
                t0.append(seconds)
                number_warning.append(0)
                broken_track.append(0)

            if debug or vidExport:
                # tracking line
                for i in range(len(tracker.tracks)):
                    if (len(tracker.tracks[i].trace) > 1):
                        for j in range(len(tracker.tracks[i].trace)-1):
                            # trace line
                            x1_trace = tracker.tracks[i].trace[j][0][0]
                            y1_trace = tracker.tracks[i].trace[j][1][0]
                            x2 = tracker.tracks[i].trace[j+1][0][0]
                            y2 = tracker.tracks[i].trace[j+1][1][0]
                            clr = tracker.tracks[i].track_id % 9
                            cv2.line(frame, (int(x1_trace), int(y1_trace)), (int(x2), int(y2)),
                                    track_colors[clr], 1)

                            # trackID
                            # text = f"{tracker.getTrackID()}"
                            cv2.putText(frame, str(displayTrackID), (int(x2), int(
                                y2)), cv2.FONT_HERSHEY_SIMPLEX, 1, track_colors[clr], 1, cv2.LINE_AA)

                # display final output
                if debug:
                    display(frame, "Tracking", final=True)

                k = cv2.waitKey(30)  # how fast vidPath plays. 42 is normal speed
                if k == 27:  # esc for end vidPath
                    break
                if k == 112:  # p for pause
                    pause = not pause
                    if pause:
                        print("paused")
                        while (pause):
                            k = cv2.waitKey(1)
                            if k == 112:
                                pause = False
                                print("resume")
                                break
                            if k == 27:
                                break
        else:
            no_ant_counter_frames += 1

        if vidExport:
            video_writer.write(frame)

    # destroy windows when done
    cap.release()
    cv2.destroyAllWindows()
    if vidExport:
        video_writer.release()

    # making csv
    full_list = list(zip(filename, ant_id, x0, y0, t0, x1,
                     y1, t1, number_warning, broken_track))
    # filename:0, ant_id:1, x0:2, y0:3, t0:4, x1:5, y1:6, t1:7, number_warning:8, broken_track:9
    
    # determine number_warning
    times = collections.deque()
    for i in range(1, len(full_list)):
        vid, idnum, x0, y0, t0, x1, y1, t1, flag, brokentrack = full_list[i]
        times.append((float(t1), i))
        while times[0][0] <= float(t1)-5:
            times.popleft()
        if len(times) >= count_warning_threshold:
            print('Warning: detected an unexpected number of tracks at '
                    f't={t1} in {vidPath}')
            for t, index in times:
                full_list[index, 8] = 1
    
    headers = ["filename", "id", "x0", "y0", "t0", "x1",
               "y1", "t1", "number_warning", "broken_track"]
    
    with open(result_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)  # Write the headers
        writer.writerows(full_list)  # Write the data rows
