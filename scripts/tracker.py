# Borrowed Heavily From Srini Ananthakrishnan's Multi Object Tracking Model
# https://github.com/srianant/kalman_filter_multi_object_tracking

import numpy as np
from kalman_filter import KalmanFilter
from scipy.optimize import linear_sum_assignment
import track_one_clip
from math import sqrt
from bisect import insort  # append to list in order

# REMEMBER, HISTORY KEEPS CONTAINS INFORMATION OF ALL ANTS
# ACTIVE_ANTS ONLY CONTAINS INFORMATION OF ACTIVE ANTS (IE ANTS THAT ARE OR RECENTLY WERE DETECTED)
class History:
    # track number of history objects (and therefore ants) created
    history_num = 0

    def __init__(self, prediction, trackIdCount):  # note that track_id and index for self.histories is the exact same
        self.filename = ''  
        self.id = trackIdCount  # identification number for each ant. this number is the same as the index in History

        # (x0, y0) is the coordinate the ant was first detected
        self.x0 = -1  
        self.y0 = -1
        self.t0 = track_one_clip.current_timestamp  # time ant was first detected

        # (x1, y1) is the coordinate the ant was last detected
        self.x1 = -1
        self.y1 = -1
        self.t1 = -1.00  # time ant was last detected

        self.number_warning = 0  # triggers if there are too many ants detected in a short amount of time (triggered in combinetrack.py)
        self.broken_track = 0  # triggers if the track was "broken", or if there was a large gap in distance between detections

        self.KF = KalmanFilter()  # KF instance to track this object
        self.prediction = np.asarray(prediction)  # predicted centroids (x,y)
        self.track_id = trackIdCount  # identification of each track object
        
        self.frame_last_seen = track_one_clip.frame_counter  # continuously updated with each detection
        self.time_last_seen = track_one_clip.current_timestamp
        self.frame_first_seen = track_one_clip.frame_counter  # frame first detected
        self.time_first_seen = track_one_clip.current_timestamp
        self.first_shoutout = False  # used to print when ant was first detected
        
        self.trace = []  # trace path
        self.area_total = 0  # used to calculate average area
        self.area_list = []  # used to calculate average area and median area
        self.average_area = 0 
        self.area = -1  # the area of the ant currently
        self.median_area = -1
        self.change_in_area_list = []  # CHANGE in area, not area itself
        self.change_in_area_max = -1  # records sudden positive spikes in change in area 
        self.change_in_area_min = 1000000  # records sudden negative spikes in change in area 

        self.exists_on_frame = True  # true if ant was detected on that frame
        self.appear_middle_begin = False  # true if ant first appeared in the middle of frame
        self.appear_middle_end = False  # true if ant fully disappeared in the middle of frame

        self.merge_list = []  # contains ant IDs this ant may have merged with (it also means this ant is still being tracked, while the merged ant is not)
        self.merge_time = []  # times where mergers may have occured
        self.unmerge_list = []  # contains ant IDs this ant may have unmerged with
        self.unmerge_time = []  # times where unmergers may have occured
        self.attached_to_me = 0  # number of ants currently attached (merged) with this ant

        self.first_merge_time = -1  # time the first merger happened (used to make merger and merger_annotation videos)
        self.last_unmerge_time = -1

        History.history_num += 1


class Active_Track:  # active ant
    
    def __init__(self, prediction, trackIdCount):  # note that track_id and index for self.histories is the exact same
        self.filename = ''
        self.id = trackIdCount
        self.x0 = -1
        self.y0 = -1
        self.t0 = track_one_clip.current_timestamp
        self.x1 = -1
        self.y1 = -1
        self.t1 = -1.00
        self.number_warning = 0
        self.broken_track = 0

        # aspects of active ant
        self.KF = KalmanFilter()  # KF instance to track this object
        self.prediction = np.asarray(prediction)  # predicted centroids (x,y)
        self.track_id = trackIdCount  # identification of each track object
        
        self.frame_last_seen = track_one_clip.frame_counter  # continuously updated with each detection
        self.time_last_seen = track_one_clip.current_timestamp
        self.frame_first_seen = track_one_clip.frame_counter  # frame first detected
        self.time_first_seen = track_one_clip.current_timestamp
        self.first_shoutout = False  # used to print when ant was first detected
        
        self.trace = []  # trace path
        self.area_total = 0
        self.area_list = []
        self.average_area = 0
        self.area = -1  # the area of the ant currently
        self.median_area = -1
        self.change_in_area_list = []
        self.change_in_area_max = -1
        self.change_in_area_min = 1000000

        self.exists_on_frame = True
        self.appear_middle_begin = False
        self.appear_middle_end = False

        self.merge_list = []
        self.merge_time = []
        self.unmerge_list = []
        self.unmerge_time = []
        self.attached_to_me = 0

        self.first_merge_time = -1
        self.last_unmerge_time = -1


class Tracker:
    def __init__(self, dist_thresh, max_trace_length, merge_distance):
        """
            dist_thresh: distance threshold. When exceeds the threshold,
                         track will be deleted and new track is created
            max_trace_length: trace path history length
            tracks: moniters active tracks and manages each tracks' data
            histories: moniters all previous and current tracks
            trackIdCount: identification of each track object
        """

        self.dist_thresh = dist_thresh
        self.max_trace_length = max_trace_length
        self.merge_distance = merge_distance
        self.tracks = []  # ACTIVE TRACKS
        self.histories = []
        self.trackIdCount = 0


    @staticmethod
    # updates the history object to be the same as the active track object
    def copy_track_to_history(history, active_track):
        history.filename = active_track.filename
        history.id = active_track.id
        history.x0 = active_track.x0
        history.y0 = active_track.y0
        history.t0 = active_track.t0
        history.x1 = active_track.x1
        history.y1 = active_track.y1
        history.t1 = active_track.t1
        history.number_warning = active_track.number_warning
        history.broken_track = active_track.broken_track
        history.frame_last_seen = active_track.frame_last_seen
        history.time_last_seen = active_track.time_last_seen
        history.frame_first_seen = active_track.frame_first_seen
        history.time_first_seen = active_track.time_first_seen
        history.first_shoutout = active_track.first_shoutout
        history.trace = active_track.trace
        history.area_total = active_track.area_total
        history.area_list = active_track.area_list
        history.average_area = active_track.average_area
        history.area = active_track.area
        history.median_area = active_track.median_area
        history.change_in_area_list = active_track.change_in_area_list
        history.change_in_area_max = active_track.change_in_area_max
        history.change_in_area_min = active_track.change_in_area_min
        history.exists_on_frame = active_track.exists_on_frame
        history.appear_middle_begin = active_track.appear_middle_begin
        history.appear_middle_end = active_track.appear_middle_end
        history.merge_list = active_track.merge_list
        history.merge_time = active_track.merge_time
        history.unmerge_list = active_track.unmerge_list
        history.unmerge_time = active_track.unmerge_time
        history.attached_to_me = active_track.attached_to_me
        history.first_merge_time = active_track.first_merge_time
        history.last_unmerge_time = active_track.last_unmerge_time

        return history


    def Update(self, centers, areas):
        # Create tracks if no tracks vector found
        if (len(self.tracks) == 0):
            for i in range(len(centers)):
                track = Active_Track(centers[i], self.trackIdCount)
                history = History(centers[i], self.trackIdCount)
                self.trackIdCount += 1
                self.tracks.append(track)
                self.histories.append(history)


        # Calculate cost using sum of square distance between
        # predicted vs detected centroids
        N = len(self.tracks)
        M = len(centers)
        cost = np.zeros(shape=(N, M))   # Cost matrix
        for i in range(len(self.tracks)):
            for j in range(len(centers)):
                try:
                    diff = self.tracks[i].prediction - centers[j]
                    distance = np.sqrt(diff[0][0]**2 + diff[1][0]**2)
                    cost[i][j] = distance
                except:
                    pass

        cost = 0.5 * cost  # average squared ERROR
        # Hungarian Algorithm: assign correct detected measurements to predict tracks
        
        global assignment
        assignment = []
        for _ in range(N):
            assignment.append(-1)
        row_ind, col_ind = linear_sum_assignment(cost)
        for i in range(len(row_ind)):
            assignment[row_ind[i]] = col_ind[i]

        # Identify tracks with no assignment, if any
        un_assigned_tracks = []
        for i in range(len(assignment)):
            if (assignment[i] != -1):
                if cost[i][assignment[i]] > self.dist_thresh:
                    assignment[i] = -1
                    un_assigned_tracks.append(i)

                # update frame_last_seen and time_last_seen
                self.tracks[i].frame_last_seen = track_one_clip.frame_counter
                self.tracks[i].time_last_seen = track_one_clip.current_timestamp
                self.tracks[i].exists_on_frame = True

        # Deletion of tracks done in track_one_clip

        # Now look for un_assigned detects
        un_assigned_detects = []
        for i in range(len(centers)):
            if i not in assignment:
                un_assigned_detects.append(i)

        # Start new tracks
        # Also start new history
        if (len(un_assigned_detects) != 0):
            for i in range(len(un_assigned_detects)):
                track = Active_Track(centers[un_assigned_detects[i]], self.trackIdCount)
                history = History(centers[i], self.trackIdCount)
                self.trackIdCount += 1
                self.tracks.append(track)
                self.histories.append(history)

        # Update KalmanFilter state, lastResults and tracks trace
        for i in range(len(assignment)):
            self.tracks[i].KF.predict()

            if (assignment[i] != -1):
                # self.tracks[i].skipped_frames = 0
                self.tracks[i].prediction = self.tracks[i].KF.correct(centers[assignment[i]], 1)
                
                change = areas[assignment[i]] - self.tracks[i].area
                self.tracks[i].change_in_area_list.append(change)

                if len(self.tracks[i].change_in_area_list) >= round(track_one_clip.fps):  # keeps area limited
                    self.tracks[i].change_in_area_list.pop(0)

                # get max and min area in average list
                self.tracks[i].change_in_area_max = max(self.tracks[i].change_in_area_list)
                self.tracks[i].change_in_area_min = min(self.tracks[i].change_in_area_list)

                self.tracks[i].area = areas[assignment[i]]

                # print(f"ANT ID: {self.tracks[i].track_id}. AREA: {self.tracks[i].area}")
                
                self.tracks[i].area_total += self.tracks[i].area
                insort(self.tracks[i].area_list, self.tracks[i].area)
                self.tracks[i].average_area = round(self.tracks[i].area_total / len(self.tracks[i].area_list), 2)

                # calculate median area
                self.tracks[i].median_area = self.tracks[i].area_list[len(self.tracks[i].area_list) // 2]

            else:
                self.tracks[i].prediction = self.tracks[i].KF.correct(np.array([[0], [0]]), 0)
                self.tracks[i].area = 0  # since not detected, area must be zero
                # though if needed, we can change this to previously recorded area
            if (len(self.tracks[i].trace) > self.max_trace_length):
                for j in range(len(self.tracks[i].trace) - self.max_trace_length):
                    del self.tracks[i].trace[j]

            self.tracks[i].trace.append(self.tracks[i].prediction)
            self.tracks[i].KF.lastResult = self.tracks[i].prediction
            fps = round(track_one_clip.fps)

            # we are now detecting potential mergers
            if self.tracks[i].change_in_area_max >= self.tracks[i].median_area // 2:
                change_location = tuple(int(value[0]) for value in self.tracks[i].trace[-1])  # return last place seen (x, y)

                # looking for ant that has recently disappeared for awhile
                # this ant may still be considered an active track, it just wasn't seen
                for j in range(len(self.tracks)):
                    if fps > track_one_clip.frame_counter - self.tracks[j].frame_last_seen > fps // 4: 
                        lost_location = tuple(int(value[0]) for value in self.tracks[j].trace[-1])

                        x = abs(change_location[0] - lost_location[0])
                        y = abs(change_location[1] - lost_location[1])
                        # calculate distance between existing ant and ant that just disappeared
                        distance = sqrt(x**2 + y**2)

                        if distance < self.merge_distance:  # if the distance is less than merge_distance, append it
                            if self.tracks[j].track_id not in self.tracks[i].merge_list and self.tracks[i].track_id != self.tracks[j].track_id:

                                # A RECOMMENDATION
                                # if needed, you might want to append self.tracks[j]'s merge_list items as well (if they exist)
                                # basically tracks[i] will inherit the merged values of tracks[j]
                                self.tracks[i].merge_list.append(self.tracks[j].track_id)  
                                self.tracks[i].merge_time.append(track_one_clip.current_timestamp)

                                if self.tracks[i].first_merge_time == -1 or self.tracks[i].attached_to_me == 0:
                                    self.tracks[i].first_merge_time = track_one_clip.current_timestamp

                                self.tracks[i].attached_to_me += 1  # increment attached_to_me, as we confirmed there was a merger

                                print(f"MERGER: Ant {self.tracks[i].track_id} got bigger and Ant {self.tracks[j].track_id} got absorbed! "
                                      "merge set", self.tracks[i].merge_list, "time", self.tracks[i].merge_time)


            # detecting potential unmergers
            if self.tracks[i].change_in_area_min <= -1 * self.tracks[i].median_area // 4:  # an ant recently lost a lot of area
                try:
                    change_location = tuple(int(value[0]) for value in self.tracks[i].trace[-1])  # return last place seen (x, y)
                    for j in range(len(self.tracks)):
                        if fps > track_one_clip.frame_counter - self.tracks[j].frame_first_seen > fps // 4:   # another ant just recently appeared
                            lost_location = tuple(int(value[0]) for value in self.tracks[j].trace[-1])

                            # find distance between these two ants
                            x, y = abs(change_location[0] - lost_location[0]), abs(change_location[1] - lost_location[1])
                            distance = sqrt(x**2 + y**2)

                            # if first ant was considered "merged" and distance is small enough
                            # attached to me doesn't have to be greater than 0
                            # and self.tracks[i].attached_to_me > 0 (REMOVED)
                            if distance < self.merge_distance * 2 and self.tracks[i].attached_to_me > 0:  # change me
                                if self.tracks[j].track_id not in self.tracks[i].unmerge_list and self.tracks[i].track_id != self.tracks[j].track_id:
                                    self.tracks[i].unmerge_list.append(self.tracks[j].track_id)
                                    self.tracks[i].unmerge_time.append(track_one_clip.current_timestamp)

                                    # in theory, unmergers should only happen AFTER a merger
                                    # but its possible a recently unmerged clump of ants unmergers once again
                                    # this serves as a warning
                                    # it's also possible a group of ants entered merged, then unmerged
                                    if self.tracks[i].attached_to_me > 0:
                                        self.tracks[i].attached_to_me -= 1
                                    else:
                                        print("WARNING: ant", self.tracks[i].begin_middle, "unmerged even though no merger was detected")  # check if it began in the middle
                                        # more code should be added here indicating what to do in this situation. current implementation
                                        # only prints a warning

                                    if self.tracks[i].attached_to_me == 0:  # ant is now considered "not merged"
                                        self.tracks[i].last_unmerge_time = track_one_clip.current_timestamp

                                        track_one_clip.merge_times.append((self.tracks[i].first_merge_time, self.tracks[i].last_unmerge_time))
                                        self.tracks[i].first_merge_time = -1
                                        self.tracks[i].last_unmerge_time = -1
                                    
                                    print(f"UNMERGER: Ant {self.tracks[i].track_id} got smaller and Ant {self.tracks[j].track_id} appeared! "
                                          "unmerge set", self.tracks[i].unmerge_list, "time", self.tracks[i].unmerge_time)
                except Exception as e:
                    # print("ERROR UNMERGE", e)
                    pass
                    
        # copy to history
        temp_id = self.tracks[i].track_id
        Tracker.copy_track_to_history(self.histories[temp_id], self.tracks[i])