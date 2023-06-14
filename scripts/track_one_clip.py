# Borrowed Heavily From Srini Ananthakrishnan's Multi Object Tracking Model
# https://github.com/srianant/kalman_filter_multi_object_tracking

import cv2
from detector import Detector, display
from tracker import Tracker
import tracker
import collections
import csv
import os
from math import floor, ceil


def trackOneClip(
        source, vidPath, vidExport, result_path, minBlob, count_warning_threshold,
        num_gaussians, invisible_threshold, min_duration,
        canny_threshold_one, canny_threshold_two, canny_aperture_size,
        thresholding_threshold, dilating_matrix, tracker_distance_threshold,
        tracker_trace_length, no_ant_counter_frames_total, edge_border, debug):
    
    cap = cv2.VideoCapture(source)

    global fps
    width, height, fps = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(
        cv2.CAP_PROP_FRAME_HEIGHT)), int(cap.get(cv2.CAP_PROP_FPS))
    size = (width, height)
    print("The size of the video is", size)

    detector = Detector(minBlob, num_gaussians, canny_threshold_one, canny_threshold_two,
                        canny_aperture_size, thresholding_threshold, dilating_matrix, debug)
    
    tracker_object = Tracker(tracker_distance_threshold, tracker_trace_length, 
                             0, no_ant_counter_frames_total)

    global frame_counter
    frame_counter = 0

    x_bound_left, x_bound_right = edge_border, width - edge_border
    y_bound_bottom, y_bound_top = edge_border, height - edge_border
    print(f"The borders are {(x_bound_left, y_bound_bottom)} to {(x_bound_right, y_bound_top)}\n")

    track_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
                    (0, 255, 255), (255, 0, 255), (255, 127, 255),
                    (127, 0, 255), (127, 0, 127)]

    pause, seconds = False, 0.00

    multiple_ant_detector = []
    multiple_ant_start = 0.00
    multiple_ant_end = 0.00
    multiple_lock = False

    if vidExport:  # saves video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # codec
        vidPath = os.path.join(vidPath, os.path.splitext(os.path.basename(source))[0] + '.mp4')
        print("The video path is", vidPath)
        video_writer = cv2.VideoWriter(vidPath, fourcc, fps, size)
        

    while (True):
        ret, frame = cap.read()  # read frame
        if not ret:
            break  # done with source

        global current_timestamp
        current_timestamp = round(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000, 2)  # current timestamp in seconds

        centers = detector.Detect(frame)  # each ant

        # LAST SEEN
        for i in range(len(tracker_object.tracks)):
            try:
                # if active ant hasn't been seen in a while
                if frame_counter - tracker_object.tracks[i].frame_last_seen > no_ant_counter_frames_total:
                    time_last_seen = round(current_timestamp - no_ant_counter_frames_total / fps, 2)
                    place_last_seen = tuple(int(value[0]) for value in tracker_object.tracks[i].trace[-1])
                    track_id = tracker_object.tracks[i].track_id

                    print(f"Ant {track_id} last seen {place_last_seen} at time {time_last_seen}")

                    tracker_object.histories[track_id].x1 = place_last_seen[0]
                    tracker_object.histories[track_id].y1 = place_last_seen[1]
                    tracker_object.histories[track_id].t1 = time_last_seen

                    if x_bound_left <= place_last_seen[0] <= x_bound_right and y_bound_bottom <= place_last_seen[1] <= y_bound_top:
                        print(f"CAUSE FOR DELETION: Ant {track_id} disappeared in the middle")
                        tracker_object.histories[track_id].do_not_include = True

                    # MIN DURATION
                    time_first_seen = tracker_object.tracks[i].time_first_seen
                    if time_last_seen - time_first_seen <= min_duration:
                        print(f'CAUSE FOR DELETION: Ant {track_id} did not exist for a minimum duration '
                              f'of {min_duration} seconds. Instead, it appeared for '
                              f'{round(time_last_seen - time_first_seen, 2)} seconds')
                        tracker_object.histories[track_id].do_not_include = True
                        
                    print("Number of Histories", tracker.History.history_num)

                    # DELETE THE TRACK!!!
                    print(f"Removed ant {tracker_object.tracks[i].track_id} from tracks list\n")
                    del tracker_object.tracks[i]
                    del tracker.assignment[i]
            except:
                pass

        # for when ants are detected
        if len(centers) > 0:


            tracker_object.Update(centers)  # track using Kalman

            seconds = round(frame_counter / fps, 2)
            timestamp_text = f"{seconds}"

            # threshold for too many ants

            if len(centers) > 1 and not multiple_lock:
                print(f"Multiple ants detected at time {current_timestamp}: Please make sure everything looks right!")
                multiple_ant_start = current_timestamp
                multiple_lock = True
            elif len(centers) == 1 and multiple_lock:
                print(f"Multiple ants no longer detected starting from time {current_timestamp}")
                multiple_ant_end = current_timestamp
                multiple_ant_detector.append((multiple_ant_start, multiple_ant_end))
                multiple_lock = False

            if len(centers) > count_warning_threshold:
                print(f"WARNING: {len(centers)} ants detected at time {current_timestamp}")

            if debug or vidExport:
                cv2.putText(frame, str(current_timestamp), (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, .4, (0, 255, 0), 2)
                

            ### NEW FIRST SEEN
            for i in range(len(tracker_object.tracks)):
                try:
                    if tracker_object.tracks[i].first_shoutout:
                        continue
                    else:
                        time_first_seen = current_timestamp
                        place_first_seen = tuple(int(value[0]) for value in tracker_object.tracks[i].trace[3])  # we don't do trace[0] because of weird glitch
                        track_id = tracker_object.tracks[i].track_id

                        print(f"Ant {track_id} first seen: {place_first_seen} at time {time_first_seen}")
                        tracker_object.tracks[i].first_shoutout = True

                        if x_bound_left <= place_first_seen[0] <= x_bound_right and y_bound_bottom <= place_first_seen[1] <= y_bound_top:
                            print(f"CAUSE FOR DELETION: Ant {track_id} appeared in the middle")
                            tracker_object.histories[track_id].do_not_include = True

                        start = os.path.abspath(__file__)   # relative path of source
                        relative_path = os.path.relpath(source, start)

                        tracker_object.histories[track_id].filename = relative_path
                        tracker_object.histories[track_id].x0 = place_first_seen[0]
                        tracker_object.histories[track_id].y0 = place_first_seen[1]
                        tracker_object.histories[track_id].t0 = time_first_seen
                                                
                except:                                           
                    pass

            if debug or vidExport:
                # tracking line
                for i in range(len(tracker_object.tracks)):
                    if (len(tracker_object.tracks[i].trace) > 1):
                        for j in range(len(tracker_object.tracks[i].trace)-1):
                            # trace line
                            x1_trace = tracker_object.tracks[i].trace[j][0][0]
                            y1_trace = tracker_object.tracks[i].trace[j][1][0]
                            x2 = tracker_object.tracks[i].trace[j+1][0][0]
                            y2 = tracker_object.tracks[i].trace[j+1][1][0]
                            clr = tracker_object.tracks[i].track_id % 9
                            cv2.line(frame, (int(x1_trace), int(y1_trace)), (int(x2), int(y2)),
                                     track_colors[clr], 1)

                            text = tracker_object.tracks[i].track_id  # track_id
                            # text = tuple(int(value[0]) for value in tracker_object.tracks[i].trace[-1])  # coordinates
                            
                            cv2.putText(frame, str(text), (int(x2), int(
                                y2)), cv2.FONT_HERSHEY_SIMPLEX, .5, track_colors[clr], 1, cv2.LINE_AA)

                display(frame, "Tracking", final=True)  # final

                video_writer.write(frame)

                speed_of_playback = 1
                k = cv2.waitKey(speed_of_playback)  # playback speed
                if k == 27:  # esc: terminate
                    break
                if k == 112:  # p: pause
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
        frame_counter += 1

    cap.release()  # destroy windows
    cv2.destroyAllWindows()
    if vidExport:
        video_writer.release()

    # determine number_warning
    full_list = []
    for history in tracker_object.histories:

        # make this look prettier
        begin_val = history.x0 == -1 or history.y0 == -1 or history.t0 == -1.00
        end_val = history.x1 == -1 or history.y1 == -1 or history.t1 == -1.00
        if begin_val or end_val or history.do_not_include:
            print(f"DELETED: Ant {history.id}")
            if begin_val:
                print(f"Looks like Ant {history.id}'s track was way too short.")
            continue
        full_list.append([history.filename, history.id, history.x0, history.y0,
                         history.t0, history.x1, history.y1, history.t1,
                         history.number_warning, history.broken_track])


    # determine number_warning
    times = collections.deque()
    for i in range(1, len(full_list)):
        _, _, _, _, _, _, _, t1, _, _ = full_list[i]
        times.append((float(t1), i))
        while times[0][0] <= float(t1)-5:
            times.popleft()
        if len(times) >= count_warning_threshold:
            print('Warning: detected an unexpected number of tracks at '
                  f't={t1} in {source}')
            for t, index in times:
                full_list[index, 8] = 1

    # for LINUX
    headers = ["filename", "id", "x0", "y0", "t0", "x1",
               "y1", "t1", "number_warning", "broken_track"]
    print("csv_file_path is", result_path)

    with open(result_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)  # Write the headers
        writer.writerows(full_list)  # Write the data rows

    if len(multiple_ant_detector) != 0:
        merged_multiple_times = merge_times(multiple_ant_detector, min_duration)
        adjusted_merged_times = adjust_time(merged_multiple_times)

        video = result_path.split("/")[2].split(".")[0]
        multi_vid_output = f"intermediate/multiples/{video}/"
        save_multi_videos(adjusted_merged_times, source, multi_vid_output)
    else:
        print("Congrats: No Multiple Ants")


def merge_times(times, time_of_multiple):
    merged_times = []
    threshold = 3  # within 3 seconds for merge
    start_time, end_time = times[0]

    for i in range(1, len(times)):
        next_start_time, next_end_time = times[i]

        if next_start_time - end_time <= threshold:
            end_time = max(end_time, next_end_time)  # Update the end time if the next interval's end time is later
        else:
            merged_times.append((start_time, end_time))
            start_time, end_time = next_start_time, next_end_time

    merged_times.append((start_time, end_time))  # Append the last merged time

    for i in range(len(merged_times)):
        time_of_multiple = 0.25
        start, end = merged_times[0]
        if end - start <= time_of_multiple:
            print("Removed instance of multiple ants (probably a blip)")
            del merged_times[i]
            i -= 1

    print(merged_times)
    return merged_times


def adjust_time(list_of_times):
    adjusted_time = []
    for start_time, end_time in list_of_times:
        start_time = floor(start_time) - 1
        end_time = ceil(end_time) + 1
        adjusted_time.append((start_time, end_time))
    return adjusted_time


def save_multi_videos(adjusted_times, vid_input, multi_vid_output):  # using ffmpeg
    counter = 0
    for time in adjusted_times:
        final_multi_output = multi_vid_output + f"multiple_{str(counter)}.mp4"
        from_time, to_time = time
        ffmpeg_command = f'ffmpeg -i {vid_input} -ss {from_time} -to {to_time} -c copy -loglevel error {final_multi_output}'
        print("Saving parts of the video with multiple ants in", final_multi_output)
        os.system(ffmpeg_command)

        counter += 1
