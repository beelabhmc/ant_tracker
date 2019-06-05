function trainingImageLabeler(varargin)
%trainingImageLabeler Label images for training a classifier.
%   trainingImageLabeler invokes an app for labeling ground truth data in images.
%   This app is used to interactively specify rectangular Regions of Interest (ROIs)
%   that define locations of objects used to train a classifier. It outputs training
%   data in a format supported by the trainCascadeObjectDetector function which is
%   used to train a model for vision.CascadeObjectDetector detector.
%
%   trainingImageLabeler(imageFolder) invokes the app and immediately
%   loads the images from imageFolder.
%
%   trainingImageLabeler(sessionFile) invokes the app and immediately loads a
%   saved image labeler session. sessionFile is the path to the MAT file
%   containing the saved session.
%
%   trainingImageLabeler CLOSE closes all open apps.
%
%   See also trainCascadeObjectDetector, vision.CascadeObjectDetector

%   Copyright 2012 The MathWorks, Inc.

%   This file is copied directly from the MATLAB R2016b source code

shouldOpenSession = false;
shouldAddImages = false;
issueWarning = false;
narginchk(0,1);

if nargin == 0
    % Create a new Training Data Labeler
    tool = vision.internal.cascadeTrainer.tool.TrainingDataLabelerTool();
    % Render the tool on the screen
    tool.show();
    return;
    
else
    validateattributes(varargin{1}, {'char'}, {'vector'}, mfilename, 'input name');
    % A single argument means either 'close' or load the images from a folder or load a session.
    if(strcmpi(varargin{1}, 'close'))
        % Handle the 'close' request
        vision.internal.cascadeTrainer.tool.TrainingDataLabelerTool.deleteAllTools();
        return;
        
    elseif exist(varargin{1}, 'dir')
        % Load images from a folder
        folder = varargin{1};
        folder = vision.internal.getFullPath(folder);
        imgSet = imageSet(folder);
        fileNames = imgSet.ImageLocation;
        if(isempty(fileNames))
            % Folder does not contain any valid images
            issueWarning = true;
        else
            shouldAddImages = true;
        end
        
    elseif exist(varargin{1}, 'file') || exist([varargin{1}, '.mat'], 'file')
        % Load a session
        sessionFileName = varargin{1};
        import vision.internal.calibration.tool.*;
        [sessionPath, sessionFileName] = parseSessionFileName(sessionFileName);
        shouldOpenSession = true;
        
    else
        error(message('vision:trainingtool:InvalidInput',varargin{1}));
    end
    
end

% Create a new Training Data Labeler
tool = vision.internal.cascadeTrainer.tool.TrainingDataLabelerTool();
tool.show();

if issueWarning
    warndlg(...
        getString(message('vision:trainingtool:NoImagesFoundMessage',folder)),...
        getString(message('vision:uitools:NoImagesAddedTitle')),'modal');
elseif shouldAddImages
    addImagesToSession(tool, fileNames);
elseif shouldOpenSession
    processOpenSession(tool, sessionPath, sessionFileName,false);
end

end


