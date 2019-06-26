function ants = ant_tracking(videoName, vidOut, outputVidDir, blobSize, ...
                             numGaussians, numTrainingFrames, ...
                             minimumBackgroundRatio, costOfNonAssignment, ...
                             invisibleForTooLong, ageThreshold, ...
                             visibilityThreshold, kalmanInitialError, ...
                             kalmanMotionNoise, kalmanMeasurementNoise, ...
                             minVisibleCount)
% vidOut - boolean, whether we should export the result video
% blobSize - int, minimum blob area in pixels
% videoName - string, absolute path to cropped vid
% outputVidDir - string, path to the directory in which to store result videos
% ants - array, the output of the function
ants =[];
if vidOut
    % split videoName into array containing path and extension
    % shouldn't this cause problems if our paths have more than one dot in them?
    videoNameSplit = strsplit(videoName,'.');
    % split videoName by / char
    videoNameString = strsplit(string(videoNameSplit(1)),'/');
    % create path name for result video
    pathname = strjoin([outputVidDir string(videoNameString(end))],'');
    % initialize mask and real result video files for later use
    v = VideoWriter(char(strjoin([pathname 'mask'], '_')));
    w = VideoWriter(char(strjoin([pathname 'real'], '_')));
    open(v);
    open(w);
end


% reader reads the video given to the function and returns the frames,
% one by one.
reader = vision.VideoFileReader(videoName);

% Uses the beginning of the video to identify the background colors and
% then compares each frame to that to identify the foreground as anything
% that isn't the background.
% We assume that any detected foreground pixels are ants.
detector = vision.ForegroundDetector('NumGaussians', numGaussians, ...
    'NumTrainingFrames', numTrainingFrames, ...
    'MinimumBackgroundRatio', minimumBackgroundRatio);

% The blob analyser detects continuous regions of pixels and identifies
% each continuous blob as being one ant.
blobAnalysis = vision.BlobAnalysis('BoundingBoxOutputPort', true, ...
    'AreaOutputPort', true, 'CentroidOutputPort', true, ...
    'MinimumBlobArea', blobSize);

% Create two video players, one to display the video,
% and one to display the foreground mask.
% maskPlayer = vision.VideoPlayer('Position', [740, 400, 700, 400]);
% videoPlayer = vision.VideoPlayer('Position', [20, 400, 700, 400]);

% id : the integer ID of the track
% bbox : the current bounding box of the object; used for display
% kalmanFilter : a Kalman filter object used for motion-based tracking
% age : the number of frames since the track was first detected
% totalVisibleCount : the total number of frames in which the track was
%                     detected (visible)
% consecutiveInvisibleCount : the number of consecutive frames for
%                             which the track was not detected (invisible)
tracks = struct(...
    'id', {}, ...                       % A unique integer ID
    'bbox', {}, ...                     % The bounding box of this track in
    ...                                 % the most recent frame
    'kalmanFilter', {}, ...             % An instance of the kalman filter for
    ...                                 % this track
    'age', {}, ...                      % The number of frames since this
    ...                                 % object was first seen
    'totalVisibleCount', {}, ...        % The number of frames in which this
    ...                                 % object has been seen
    'consecutiveInvisibleCount', {} ... % The current streak of frames since
    ...                                 % this object was last seen
);

nextId = 1; % ID of the next track
frameNumber = 1;

% Detect moving objects, and track them across video frames.
while ~isDone(reader)
    frame = reader.step();
    [centroids, bboxes, mask] = detectObjects(frame);
    tracks = predictNewLocationsOfTracks(tracks);
    [assignments, unassignedTracks, unassignedDetections] = ...
        detectionToTrackAssignment(tracks, centroids);
    tracks = updateAssignedTracks(tracks, assignments);
    tracks = updateUnassignedTracks(tracks, unassignedTracks);
    tracks = deleteLostTracks(tracks);
    tracks = cat(1, tracks, transpose(createNewTracks(centroids, bboxes)));
    displayTrackingResults(tracks);
    frameNumber = frameNumber + 1;
end

function [centroids, bboxes, mask] = detectObjects(frame)

    % Detect foreground.
    mask = detector.step(frame);

    % Apply morphological operations to remove noise and fill in holes.
    % mask is a binary image
    % strel() returns a morpholigical structuring element (ie a
    % collective region of 1's in a sea of 0's)
    % the second argument to strel() specifies the shape (see
    % matlab documentation)
    % docs: https://www.mathworks.com/help/images/morphological-dilation-and-
    % erosion.html
    
    mask = imerode(mask, strel('rectangle', [4,4]));
    % mask = imdilate(mask, strel('rectangle', [1, 1]));
    % mask = imopen(mask, strel('rectangle', [3,3]));
    % mask = imclose(mask, strel('rectangle', [3, 3]));
    mask = imfill(mask, 'holes');

    % Perform blob analysis to find connected components.
    [~, centroids, bboxes] = blobAnalysis.step(mask);
end

function trackList = predictNewLocationsOfTracks(trackList)
    for i = 1:length(trackList)
        bbox = trackList(i).bbox;

        % Predict the current location of the track.
        predictedCentroid = predict(trackList(i).kalmanFilter);

        % Shift the bounding box so that its center is at
        % the predicted location.
        predictedCentroid = int32(predictedCentroid) - bbox(3:4) / 2;
        trackList(i).bbox = [predictedCentroid, bbox(3:4)];
    end
end

function [assignments, unassignedTracks, unassignedDetections] = ...
        detectionToTrackAssignment(trackList, detections)

    nTracks = length(trackList);
    nDetections = size(detections, 1);

    % Compute the cost of assigning each detection to each track.
    cost = zeros(nTracks, nDetections);
    for i = 1:nTracks
        cost(i, :) = distance(trackList(i).kalmanFilter, detections);
    end

    % Solve the assignment problem.
    [assignments, unassignedTracks, unassignedDetections] = ...
        assignDetectionsToTracks(cost, costOfNonAssignment);
end


function trackList = updateAssignedTracks(trackList, assignments)
    numAssignedTracks = size(assignments, 1);
    for i = 1:numAssignedTracks
        trackIdx = assignments(i, 1);
        detectionIdx = assignments(i, 2);
        centroid = centroids(detectionIdx, :);
        bbox = bboxes(detectionIdx, :);

        % Correct the estimate of the object's location
        % using the new detection.
        correct(trackList(trackIdx).kalmanFilter, centroid);

        % Replace predicted bounding box with detected
        % bounding box.
        trackList(trackIdx).bbox = bbox;

        % Update track's age.
        trackList(trackIdx).age = trackList(trackIdx).age + 1;

        % Update visibility.
        trackList(trackIdx).totalVisibleCount = ...
                trackList(trackIdx).totalVisibleCount + 1;
        trackList(trackIdx).consecutiveInvisibleCount = 0;
    end
end

function trackList = updateUnassignedTracks(trackList, unassigned)
    for i = 1:length(unassigned)
        ind = unassigned(i);
        trackList(ind).age = trackList(ind).age + 1;
        trackList(ind).consecutiveInvisibleCount = ...
                trackList(ind).consecutiveInvisibleCount + 1;
    end
end


function trackList = deleteLostTracks(trackList)
    if isempty(trackList)
        return;
    end

    % Compute the fraction of the track's age for which it was visible.
    ages = [trackList(:).age];
    totalVisibleCounts = [trackList(:).totalVisibleCount];
    visibility = totalVisibleCounts ./ ages;

    % Find the indices of 'lost' tracks.
    lostInds = (ages < ageThreshold & visibility < visibilityThreshold) | ...
        [trackList(:).consecutiveInvisibleCount] >= invisibleForTooLong;

    % Delete lost tracks.
    trackList = trackList(~lostInds);
end


function newTracks = createNewTracks(centroids, boxes)
    centroids = centroids(unassignedDetections, :);
    boxes = boxes(unassignedDetections, :);
    newTracks = struct(...
        'id', {}, ...
        'bbox', {}, ...
        'kalmanFilter', {}, ...
        'age', {}, ...
        'totalVisibleCount', {}, ...
        'consecutiveInvisibleCount', {} ...
    );
    for i = 1:size(centroids, 1)

        centroid = centroids(i,:);
        bbox = boxes(i, :);

        % Create a Kalman filter object.
        % parameters are:
        %    MotionModel - assumed model by which the ants move:
        %                  ConstantVelocity or ConstantAcceleration
        %    InitialLocation - a vector representing the location of the object
        %    InitialEstimateError - the variance of the initial estimates of
        %                           location and velocity of the tracked object
        %    MotionNoise - deviation of selected (ie ConstantVelocity) model
        %                  from actual model, as a 2 element vector; increase
        %                  makes Kalman filter more tolerant
        %    MeasurementNoise - tolerance for noise in detections; larger
        %                       value makes Kalman Filter less tolerant
        kalmanFilter = configureKalmanFilter('ConstantVelocity', ...
            centroid, kalmanInitialError, kalmanMotionNoise, ...
            kalmanMeasurementNoise);

        % Create a new track.
        newTrack = struct(...
            'id', nextId, ...
            'bbox', bbox, ...
            'kalmanFilter', kalmanFilter, ...
            'age', 1, ...
            'totalVisibleCount', 1, ...
            'consecutiveInvisibleCount', 0);

        % Add it to the array of tracks.
        newTracks(end + 1) = newTrack;

        % Increment the next id.
        nextId = nextId + 1;
    end
end


function displayTrackingResults(results)
    % Convert the frame and the mask to uint8 RGB.
    frame = im2uint8(frame);
    mask = uint8(repmat(mask, [1, 1, 3])) .* 255;

    if ~isempty(results)

        % Noisy detections tend to result in short-lived tracks.
        % Only display tracks that have been visible for more than
        % a minimum number of frames.
        reliableTrackInds = ...
            [results(:).totalVisibleCount] > minVisibleCount;
        reliableTracks = results(reliableTrackInds);
        % Display the objects. If an object has not been detected
        % in this frame, display its predicted bounding box.
        if ~isempty(reliableTracks)
            % Get bounding boxes.
            bboxes = cat(1, reliableTracks.bbox);

            % Get ids.
            ids = int32([reliableTracks(:).id]);

            frameNumberMat = frameNumber * ones(size(transpose(ids)));

            visible = [reliableTracks(:).consecutiveInvisibleCount] < 1;

            ants = [ants; [bboxes, transpose(ids), frameNumberMat, ...
                           transpose(visible)]];

            % Create labels for objects indicating the ones for
            % which we display the predicted rather than the actual
            % location.
            labels = cellstr(int2str(ids'));
            predictedTrackInds = ...
                [reliableTracks(:).consecutiveInvisibleCount] > 0;
            isPredicted = cell(size(labels));
            isPredicted(predictedTrackInds) = {'p'};
            labels = strcat(labels, isPredicted);

            % remove labels
            % labels = cellstr(strings(size(ids')));

            % Draw the objects on the frame.
            frame = insertObjectAnnotation(frame, 'rectangle', ...
                bboxes, labels, 'TextBoxOpacity', 0, 'FontSize', 10, ...
                'TextColor', 'red');

            % Draw the objects on the mask.
            mask = insertObjectAnnotation(mask, 'rectangle', ...
                bboxes, labels, 'TextBoxOpacity', 0, 'FontSize', 10, ...
                'TextColor', 'red');
    % Commented out these so video is only written if ants are in the frame.
    %     end
    % end
            if vidOut
                % Display the mask and the frame.
                % maskPlayer.step(mask);
                writeVideo(v,mask);
                % videoPlayer.step(frame);
                writeVideo(w,frame);
            end
        end
    end
end

if vidOut
    close(v);
    close(w);
end
return
end

