function ants = ant_tracking(vidOut, blobSize, videoName, outputVidDir)
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
    v = VideoWriter(char(strjoin([pathname 'mask'], '_')),'MPEG-4');
    w = VideoWriter(char(strjoin([pathname 'real'], '_')),'MPEG-4');
    open(v);
    open(w);
end


% Create System objects used for reading video, detecting moving objects,
% and displaying the results.
obj = setupSystemObjects();

tracks = initializeTracks(); % Create an empty array of tracks.
% each track is a structure representing a moving object in the video

nextId = 1; % ID of the next track

% Detect moving objects, and track them across video frames.
while ~isDone(obj.reader)
    frame = readFrame();
    [centroids, bboxes, mask] = detectObjects(frame);
    predictNewLocationsOfTracks();
    [assignments, unassignedTracks, unassignedDetections] = ...
        detectionToTrackAssignment();

    updateAssignedTracks();
    updateUnassignedTracks();
    deleteLostTracks();
    createNewTracks();

    displayTrackingResults();
end


function obj = setupSystemObjects()
        % Initialize Video I/O
        % Create objects for reading a video from a file, drawing the tracked
        % objects in each frame, and playing the video.

        % Create a video file reader.
        obj.reader = vision.VideoFileReader(videoName);

        % Create two video players, one to display the video,
        % and one to display the foreground mask.
%         obj.maskPlayer = vision.VideoPlayer('Position', [740, 400, 700, 400]);
%         obj.videoPlayer = vision.VideoPlayer('Position', [20, 400, 700, 400]);

        % Create System objects for foreground detection and blob analysis

        % The foreground detector is used to segment moving objects from
        % the background. It outputs a binary mask, where the pixel value
        % of 1 corresponds to the foreground and the value of 0 corresponds
        % to the background.

        obj.detector = vision.ForegroundDetector('NumGaussians', 5, ...
            'NumTrainingFrames', 40, 'MinimumBackgroundRatio', 0.75);

        % Connected groups of foreground pixels are likely to correspond to moving
        % objects.  The blob analysis System object is used to find such groups
        % (called 'blobs' or 'connected components'), and compute their
        % characteristics, such as area, centroid, and the bounding box.

        obj.blobAnalyser = vision.BlobAnalysis('BoundingBoxOutputPort', true, ...
            'AreaOutputPort', true, 'CentroidOutputPort', true, ...
            'MinimumBlobArea', blobSize); %make a parameter
end
 

function tracks = initializeTracks()
    % create an empty array of tracks, each with the following attributes:
    % id : the integer ID of the track
    % bbox : the current bounding box of the object; used for display
    % kalmanFilter : a Kalman filter object used for motion-based tracking
    % age : the number of frames since the track was first detected
    % totalVisibleCount : the total number of frames in which the track was detected (visible)
    % consecutiveInvisibleCount : the number of consecutive frames for which the track was not detected (invisible)
    tracks = struct(...
        'id', {}, ...
        'bbox', {}, ...
        'kalmanFilter', {}, ...
        'age', {}, ...
        'totalVisibleCount', {}, ...
        'consecutiveInvisibleCount', {});
end


function frame = readFrame()
    frame = obj.reader.step();
end


function [centroids, bboxes, mask] = detectObjects(frame)

    % Detect foreground.
    mask = obj.detector.step(frame);

    % Apply morphological operations to remove noise and fill in holes.
    % mask is a binary image
    % strel() returns a morpholigical structuring element (ie a collective region of 1's in a sea of 0's)
    % the second argument to strel() specifies the shape (see matlab documentation)
    % docs: https://www.mathworks.com/help/images/morphological-dilation-and-erosion.html
    
    mask = imerode(mask, strel('rectangle', [4,4]));
    mask = imdilate(mask, strel('rectangle', [2, 2]));
    % mask = imopen(mask, strel('rectangle', [3,3]));
    % mask = imclose(mask, strel('rectangle', [3, 3]));
    mask = imfill(mask, 'holes');

    % Perform blob analysis to find connected components.
    [~, centroids, bboxes] = obj.blobAnalyser.step(mask);
end

function predictNewLocationsOfTracks()
    for i = 1:length(tracks)
        bbox = tracks(i).bbox;

        % Predict the current location of the track.
        predictedCentroid = predict(tracks(i).kalmanFilter);

        % Shift the bounding box so that its center is at
        % the predicted location.
        predictedCentroid = int32(predictedCentroid) - bbox(3:4) / 2;
        tracks(i).bbox = [predictedCentroid, bbox(3:4)];
    end
end

function [assignments, unassignedTracks, unassignedDetections] = ...
        detectionToTrackAssignment()

    nTracks = length(tracks);
    nDetections = size(centroids, 1);

    % Compute the cost of assigning each detection to each track.
    cost = zeros(nTracks, nDetections);
    for i = 1:nTracks
        cost(i, :) = distance(tracks(i).kalmanFilter, centroids);
    end

    % Solve the assignment problem.
    costOfNonAssignment = 20;
    [assignments, unassignedTracks, unassignedDetections] = ...
        assignDetectionsToTracks(cost, costOfNonAssignment);
end


function updateAssignedTracks()
    numAssignedTracks = size(assignments, 1);
    for i = 1:numAssignedTracks
        trackIdx = assignments(i, 1);
        detectionIdx = assignments(i, 2);
        centroid = centroids(detectionIdx, :);
        bbox = bboxes(detectionIdx, :);

        % Correct the estimate of the object's location
        % using the new detection.
        correct(tracks(trackIdx).kalmanFilter, centroid);

        % Replace predicted bounding box with detected
        % bounding box.
        tracks(trackIdx).bbox = bbox;

        % Update track's age.
        tracks(trackIdx).age = tracks(trackIdx).age + 1;

        % Update visibility.
        tracks(trackIdx).totalVisibleCount = ...
            tracks(trackIdx).totalVisibleCount + 1;
        tracks(trackIdx).consecutiveInvisibleCount = 0;
    end
end

function updateUnassignedTracks()
    for i = 1:length(unassignedTracks)
        ind = unassignedTracks(i);
        tracks(ind).age = tracks(ind).age + 1;
        tracks(ind).consecutiveInvisibleCount = ...
            tracks(ind).consecutiveInvisibleCount + 1;
    end
end


function deleteLostTracks()
    if isempty(tracks)
        return;
    end

    invisibleForTooLong = 20;
    ageThreshold = 8;

    % Compute the fraction of the track's age for which it was visible.
    ages = [tracks(:).age];
    totalVisibleCounts = [tracks(:).totalVisibleCount];
    visibility = totalVisibleCounts ./ ages;

    % Find the indices of 'lost' tracks.
    lostInds = (ages < ageThreshold & visibility < 0.6) | ...
        [tracks(:).consecutiveInvisibleCount] >= invisibleForTooLong;

    % Delete lost tracks.
    tracks = tracks(~lostInds);
end


function createNewTracks()
    centroids = centroids(unassignedDetections, :);
    bboxes = bboxes(unassignedDetections, :);

    for i = 1:size(centroids, 1)

        centroid = centroids(i,:);
        bbox = bboxes(i, :);

        % Create a Kalman filter object.
        % parameters are:
        %    MotionModel - assumed model by which the ants move: ConstantVelocity or ConstantAcceleration
        %    InitialLocation - a vector representing the location of the object
        %    InitialEsimateError - the variance of the initial estimates of location and velocity of the tracked object
        %    MotionNoise - deviation of selected (ie ConstantVelocity) model from actual model, as a 2 element vector
        %    MeasurementNoise - tolerance for noise in detections; larger value makes Kalman Filter less tolerant
        kalmanFilter = configureKalmanFilter('ConstantVelocity', ...
            centroid, [200, 50], [100, 25], 100);

        % Create a new track.
        newTrack = struct(...
            'id', nextId, ...
            'bbox', bbox, ...
            'kalmanFilter', kalmanFilter, ...
            'age', 1, ...
            'totalVisibleCount', 1, ...
            'consecutiveInvisibleCount', 0);

        % Add it to the array of tracks.
        tracks(end + 1) = newTrack;

        % Increment the next id.
        nextId = nextId + 1;
    end
end


function displayTrackingResults()
    % Convert the frame and the mask to uint8 RGB.
    frame = im2uint8(frame);
    mask = uint8(repmat(mask, [1, 1, 3])) .* 255;

    minVisibleCount = 8;
    if ~isempty(tracks)

        % Noisy detections tend to result in short-lived tracks.
        % Only display tracks that have been visible for more than
        % a minimum number of frames.
        reliableTrackInds = ...
            [tracks(:).totalVisibleCount] > minVisibleCount;
        reliableTracks = tracks(reliableTrackInds);

        % Display the objects. If an object has not been detected
        % in this frame, display its predicted bounding box.
        if ~isempty(reliableTracks)
            % Get bounding boxes.
            bboxes = cat(1, reliableTracks.bbox);

            % Get ids.
            ids = int32([reliableTracks(:).id]);
            
            ants = [ants; [bboxes, transpose(ids)]];

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
                bboxes, labels, 'TextBoxOpacity', 0, 'FontSize', 8, 'TextColor', 'red');

            % Draw the objects on the mask.
            mask = insertObjectAnnotation(mask, 'rectangle', ...
                bboxes, labels, 'TextBoxOpacity', 0, 'FontSize', 8, 'TextColor', 'red');
        end
    end
    if vidOut
        % Display the mask and the frame.
%         obj.maskPlayer.step(mask);
        writeVideo(v,mask);
%         obj.videoPlayer.step(frame);
        writeVideo(w,frame);
    end
end

if vidOut
    close(v);
    close(w);
end
return
end
