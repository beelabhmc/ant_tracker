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
        source, vidPath, vidExport, minBlob, num_gaussians,
        canny_threshold_one, canny_threshold_two, canny_aperture_size,
        thresholding_threshold, dilating_matrix, tracker_distance_threshold,
        tracker_trace_length, no_ant_counter_frames_total, edge_border, 
        merge_distance):
    
    cap = cv2.VideoCapture(source)  # create video reader object

    # we use these variables in different python files, hence we make it global
    global width, height, fps, frame_counter, x_bound_left, x_bound_right, y_bound_bottom, y_bound_top

    # get width, height, and frames per second of video
    width, height, fps = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), cap.get(cv2.CAP_PROP_FPS)
    size = (width, height)

    # create detector object
    detector_object = Detector(minBlob, num_gaussians, canny_threshold_one, canny_threshold_two, canny_aperture_size, thresholding_threshold, dilating_matrix)

    # create tracker object
    tracker_object = Tracker(tracker_distance_threshold, tracker_trace_length, merge_distance)

    frame_counter = 0  # counts number of frames have been read by video reader

    # gets coordinates of borders of videos (this value is set by edge_border)
    x_bound_left, x_bound_right = edge_border, width - edge_border
    y_bound_bottom, y_bound_top = edge_border, height - edge_border

    # each track gets displayed in a different color (avoids confusion)
    # remember we use bgr not rgb
    track_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
                    (0, 255, 255), (255, 0, 255), (255, 127, 255),
                    (127, 0, 255), (127, 0, 127)]

    # used for debugging (local use only)
    pause = False

    # if we are exporting the video, we also create a video writer
    if vidExport:  # saves video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # codec
        video_writer_full = cv2.VideoWriter(vidPath, fourcc, fps, size)


    # current timestamp returns the time passed in the video.
    # weirdly, doing frame_counter / fps doesn't give us the same answer as current timestamp
    # so just use current timestamp for consistency sake
    global current_timestamp
    current_timestamp = 0.0


    # don't touch first_go. without it, you might get exit times that are less than
    # entry times (due to how the current pipeline works)
    first_go = False
    
    while (True):
        ret, frame = cap.read()  # read one frame
        if not ret:
            break  # frame is invalid or we are done with entire video

        # this avoids weird negative times
        temp_timestamp = round(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000, 2)
        if temp_timestamp == 0 and not first_go:
            first_go = True
            current_timestamp = temp_timestamp
        elif temp_timestamp == 0 and first_go:
            pass
        else:
            current_timestamp = temp_timestamp


        # returns ant centers and ant areas in frame (if detected)
        centers, areas = detector_object.Detect(frame)  # each ant

        # put timestamp on video
        cv2.putText(frame, str(current_timestamp), (0, 10), cv2.FONT_HERSHEY_SIMPLEX, .4, (0, 255, 0), 2)

        # checks if ant has left the frame
        for i in range(len(tracker_object.tracks)):
            try:
                track_id = tracker_object.tracks[i].track_id

                # checks if ant is seen on the frame at the moment.
                # note this might trigger if an ant has "blipped" out of existence for one frame.
                if frame_counter - tracker_object.tracks[i].frame_last_seen > 0:
                    tracker_object.tracks[i].exists_on_frame = False

                place_last_seen = tuple(int(value[0]) for value in tracker_object.tracks[i].trace[-1])

                # if the ant disappeared near the edge, we will give it no_ant_counter_frames_total number of frames 
                # to reappear. otherwise, it will be considered gone and the active track will be deleted (it will
                # still remain in the history)
                if x_bound_left <= place_last_seen[0] <= x_bound_right and y_bound_bottom <= place_last_seen[1] <= y_bound_top:  # by the border
                    gone_frames = no_ant_counter_frames_total * 1  # change scalar

                # if the ant disappeared in the middle, we will be more generous and give it no_ant_counter_frames_total
                # times 2 frames to reappear. otherwise it will be considered gone and will be flagged as "end_middle"
                # PLEASE FEEL FREE TO CHANGE THE SCALAR --> IT DOESN'T HAVE TO BE * 2
                else:  # disappeared in the middle:
                    gone_frames = no_ant_counter_frames_total * 2  # change scalar
                    
                # the ant hasn't been seen in awhile, so we will now delete its corresponding active track
                if frame_counter - tracker_object.tracks[i].frame_last_seen > gone_frames:
                    time_last_seen = round(current_timestamp - gone_frames / fps, 2)
                    place_last_seen = tuple(int(value[0]) for value in tracker_object.tracks[i].trace[-1])
                    
                    print(f"Ant {track_id} last seen {place_last_seen} at time {time_last_seen}")

                    tracker_object.tracks[i].x1 = place_last_seen[0]
                    tracker_object.tracks[i].y1 = place_last_seen[1]
                    tracker_object.tracks[i].t1 = time_last_seen

                    # if the ant disappeared within the borders of the frame dictated by edge_border
                    if x_bound_left <= place_last_seen[0] <= x_bound_right and y_bound_bottom <= place_last_seen[1] <= y_bound_top:
                        print(f"WARNING: Ant {track_id} disappeared in the middle")

                        tracker_object.tracks[i].appear_middle_end = True  # this will flag "end_middle" as true


                    # it is possible an ant leaves while merged with another ant
                    # we will assume the ants eventually unmerged, so the new unmerge time will be the time
                    # the ant was last seen
                    if tracker_object.tracks[i].attached_to_me > 0:
                        print(f"Merged ant {tracker_object.tracks[i].track_id} left. There was no unmerger")
                        tracker_object.tracks[i].unmerge_time.append(time_last_seen)


                    # we want to copy this information to its corresponding history
                    # remember every active track has its corresponding history object. 
                    # the active track's id is the SAME as the index of the histories list. 
                    Tracker.copy_track_to_history(tracker_object.histories[track_id], tracker_object.tracks[i])

                    # delete now obselete active track
                    print(f"Removed ant {tracker_object.tracks[i].track_id} from active tracks list\n")
                    del tracker_object.tracks[i]
                    del tracker.assignment[i]
            except:
                pass

        # if ants were detected on frame
        if len(centers) > 0:

            # make new updated predictions with given coordinates
            tracker_object.Update(centers, areas)

            # when ants are detected for the first time (they entered the frame for the first time)
            for i in range(len(tracker_object.tracks)):
                try:
                    # first_shoutout checks if initial information was already gathered
                    # if it has, don't gather it again (as it will override the correct information)
                    if tracker_object.tracks[i].first_shoutout:
                        continue
                    else:
                        time_first_seen = current_timestamp

                        # IMPORTANT: the place_first seen is actually NOT set to trace[0]. this is because the tracker
                        # sets the initial position quite far away from the actual ant, and takes around 2 frames
                        # for the tracker to properly adjust the position, hence trace[2]
                        place_first_seen = tuple(int(value[0]) for value in tracker_object.tracks[i].trace[2])  # we don't do trace[0] because of weird glitch
                        track_id = tracker_object.tracks[i].track_id

                        print(f"Ant {track_id} first seen: {place_first_seen} at time {time_first_seen}")
                        tracker_object.tracks[i].first_shoutout = True

                        # detects if the ant appeared in the middle (threshold determined by edge_border)
                        if x_bound_left <= place_first_seen[0] <= x_bound_right and y_bound_bottom <= place_first_seen[1] <= y_bound_top:
                            print(f"WARNING: Ant {track_id} appeared in the middle")
                            tracker_object.tracks[i].appear_middle_begin = True

                        start = os.path.abspath(__file__)   # relative path of source
                        relative_path = os.path.relpath(source, start)

                        # store relevant information
                        tracker_object.tracks[i].filename = relative_path
                        tracker_object.tracks[i].x0 = place_first_seen[0]
                        tracker_object.tracks[i].y0 = place_first_seen[1]
                        tracker_object.tracks[i].t0 = time_first_seen

                        # copy active track information to corresponding history object
                        Tracker.copy_track_to_history(tracker_object.histories[track_id], tracker_object.tracks[i])
                                                
                except:                                           
                    pass

            # we draw the id on top of the ant as well as the trace
            if vidExport:
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
                            # text = tracker_object.tracks[i].area  # area
                            
                            cv2.putText(frame, str(text), (int(x2), int(
                                y2)), cv2.FONT_HERSHEY_SIMPLEX, .5, track_colors[clr], 1, cv2.LINE_AA)

                # this won't work on the server, as there is no display corresponding to the server
                # you will need to "connect" your display with the server (you will have to look this up)
                # display(frame, "Tracking")  # good for debug

                speed_of_playback = 1
                k = cv2.waitKey(speed_of_playback)  # playback speed
                if k == 27:  # esc key: terminate
                    break
                if k == 112:  # p key: pause
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
        
        frame_counter += 1  # an advancement of a frame
        video_writer_full.write(frame)  # save frame into video writer


    cap.release()  # releases video reader
    cv2.destroyAllWindows() 
    if vidExport:
        video_writer_full.release()  # saves contents of video writer


    return tracker_object  # tracker_object contains histories


# this function writes and saves the contents of histories into a csv file
def make_history_CSV(tracker_object, history_path):
    full_list_history = []
    for history in tracker_object.histories:
        # seperate different times with a space (not a comma, remember we are using a csv)
        merge_id = ' '.join(str(element) for element in history.merge_list)
        merge_time = ' '.join(str(element) for element in history.merge_time)
        unmerge_id = ' '.join(str(element) for element in history.unmerge_list)
        unmerge_time = ' '.join(str(element) for element in history.unmerge_time)

        # set to one if middle_begin or middle_end is true
        middle_begin = 1 if history.appear_middle_begin == True else 0
        middle_end = 1 if history.appear_middle_end == True else 0

        # append row by row
        full_list_history.append([history.filename, history.id, history.x0, history.y0, history.t0, 
                    history.x1, history.y1, history.t1, middle_begin, middle_end, merge_id, merge_time,
                    unmerge_id, unmerge_time, history.number_warning, history.broken_track])
        
    headers = ["filename", "id", "x0", "y0", "t0", "x1",
               "y1", "t1", "begin_middle", "end_middle", "merge_id", "merge_time", 
               "unmerge_id", "unmerge_time", "number_warning", "broken_track"]
            
    print("The csv_history_file_path is", history_path)

    if not os.path.exists(os.path.dirname(history_path)):
        os.makedirs(os.path.dirname(history_path))

    with open(history_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)  # Write the headers
        writer.writerows(full_list_history)  # Write the data rows

    return history_path


# outputs parts of the video where mergers were detected
# there are two outputs: one annotated and one without
# this won't run if there were no merges detected
def make_merge_vids(history_csv, video_source, annotated_video_source, result_path, annotated_result_path):

    # the goal is to "combine" relatively similar times
    with open(history_csv, 'r') as file:
        reader = csv.DictReader(file)
        range_of_times = []

        for row in reader:
            # return merge_time and unmerger_time as a list
            merge_time = row.get('merge_time').split()
            unmerge_time = row.get('unmerge_time').split()

            id = row.get('id')

            if len(merge_time) > 0 and len(unmerge_time) > 0:
                first_one = True
                begin_time = 0

                for unmerge in unmerge_time:
                    unmerge = float(unmerge)
                    for merge in merge_time:
                        merge = float(merge)
                        if first_one:
                            first_one = False
                            begin_time = merge

                        # obviously this isn't possible, so we break
                        if merge > unmerge:
                            merge_time = merge_time[merge_time.index(str(merge)):]
                            # first_one = True
                            break

                    first_one = True
                    range_of_times.append((floor(begin_time) - 5, ceil(unmerge) + 5))  # we will add 5 seconds of padding

                # crops times
                if range_of_times != []:
                    for index, time in enumerate(range_of_times):
                        from_time, to_time = time

                        # calls ffmpeg to trim videos at specific times
                        final_result_path = os.path.join(result_path, id + '_' + str(index) + '.mp4')
                        ffmpeg_command = f'ffmpeg -y -i {video_source} -ss {from_time} -to {to_time} -c copy -loglevel error {final_result_path}'
                        os.system(ffmpeg_command)

                        final_annotated_result_path = os.path.join(annotated_result_path, id + '_' + str(index) + '.mp4')
                        ffmpeg_command = f'ffmpeg -y -i {annotated_video_source} -ss {from_time} -to {to_time} -c copy -loglevel error {final_annotated_result_path}'
                        os.system(ffmpeg_command)

                range_of_times = []

            else:
                print("Uh oh, there are more unmerge times and merge times. I don't know what to do!")
