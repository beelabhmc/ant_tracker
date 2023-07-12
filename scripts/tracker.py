# Borrowed Heavily From Srini Ananthakrishnan's Multi Object Tracking Model
# https://github.com/srianant/kalman_filter_multi_object_tracking

import numpy as np
from kalman_filter import KalmanFilter
from scipy.optimize import linear_sum_assignment
import track_one_clip


class History:

    # global history_num
    history_num = 0

    def __init__(self, trackIdCount):  # note that track_id and index for self.histories is the exact same
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
        self.do_not_include = False

        History.history_num += 1


class Track:
    def __init__(self, prediction, trackIdCount):
        self.KF = KalmanFilter()  # KF instance to track this object
        self.prediction = np.asarray(prediction)  # predicted centroids (x,y)
        
        self.track_id = trackIdCount  # identification of each track object  # FIXME + 1 or not?
        # self.skipped_frames = 0  # number of frames skipped undetected
        self.frame_last_seen = track_one_clip.frame_counter  # continuously updated with each detection
        self.time_last_seen = track_one_clip.current_timestamp
        self.frame_first_seen = track_one_clip.frame_counter  # frame first detected
        self.time_first_seen = track_one_clip.current_timestamp
        self.first_shoutout = False  # used to print when ant was first detected
        self.trace = []  # trace path
        self.distance_traveled = 0  # distance traveled (calculated by Manhatten Distance)


class Tracker:
    def __init__(self, dist_thresh, max_trace_length,
                 trackIdCount, no_ant_counter_frames_total):
        """
            dist_thresh: distance threshold. When exceeds the threshold,
                         track will be deleted and new track is created
            max_frames_to_skip: maximum allowed frames to be skipped for
                                the track object undetected
            max_trace_length: trace path history length
            trackIdCount: identification of each track object
        """

        self.dist_thresh = dist_thresh
        self.max_trace_length = max_trace_length
        self.tracks = []  # active tracks only
        self.histories = []
        self.trackIdCount = trackIdCount  # total number of ants seen (including falsities)
        self.no_ant_counter_frames_total = no_ant_counter_frames_total


    def Update(self, detections):
        # Create tracks if no tracks vector found
        if (len(self.tracks) == 0):
            for i in range(len(detections)):
                track = Track(detections[i], self.trackIdCount)
                history = History(self.trackIdCount)
                self.trackIdCount += 1
                self.tracks.append(track)
                self.histories.append(history)

        # Calculate cost using sum of square distance between
        # predicted vs detected centroids
        N = len(self.tracks)
        M = len(detections)
        cost = np.zeros(shape=(N, M))   # Cost matrix
        for i in range(len(self.tracks)):
            for j in range(len(detections)):
                try:
                    diff = self.tracks[i].prediction - detections[j]
                    distance = np.sqrt(diff[0][0]**2 +
                                       diff[1][0]**2)
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
                # Check distance threshold.
                if cost[i][assignment[i]] > self.dist_thresh:
                    assignment[i] = -1
                    un_assigned_tracks.append(i)
                    # self.trackIdCount -= 1
                    print("Distance Threshold Triggered")
                    print()
                self.tracks[i].frame_last_seen = track_one_clip.frame_counter
                self.tracks[i].time_last_seen = track_one_clip.current_timestamp

        # Deletion of tracks done in track_one_clip

        # Now look for un_assigned detects
        un_assigned_detects = []
        for i in range(len(detections)):
            if i not in assignment:
                un_assigned_detects.append(i)

        # Start new tracks
        # Also start new history
        if (len(un_assigned_detects) != 0):
            for i in range(len(un_assigned_detects)):
                track = Track(detections[un_assigned_detects[i]], self.trackIdCount)
                history = History(self.trackIdCount)
                self.trackIdCount += 1
                self.tracks.append(track)
                self.histories.append(history)
                print("New Ant!!! (Multiple Ants)")

        # Update KalmanFilter state, lastResults and tracks trace
        for i in range(len(assignment)):
            self.tracks[i].KF.predict()

            if (assignment[i] != -1):
                # self.tracks[i].skipped_frames = 0
                self.tracks[i].prediction = self.tracks[i].KF.correct(
                    detections[assignment[i]], 1)
            else:
                self.tracks[i].prediction = self.tracks[i].KF.correct(
                    np.array([[0], [0]]), 0)

            if (len(self.tracks[i].trace) > self.max_trace_length):
                for j in range(len(self.tracks[i].trace) -
                               self.max_trace_length):
                    del self.tracks[i].trace[j]

            self.tracks[i].trace.append(self.tracks[i].prediction)
            self.tracks[i].KF.lastResult = self.tracks[i].prediction
