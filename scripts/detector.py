# Borrowed Heavily From Srini Ananthakrishnan's Multi Object Tracking Model
# https://github.com/srianant/kalman_filter_multi_object_tracking

import numpy as np
import cv2

dis_vid = True
toDisplay = False


# please use this when running locally or connected server to your display
# this function displays a frame, but with its resolution multiplied
# this is because the original videos are extremely small. with this you
# can see properly
def display(frame, description):

    try:
        height, width = frame.shape
    except:
        height, width, _ = frame.shape

    scaler = 5

    new_width = width * scaler
    new_height = height * scaler
    resized_frame = cv2.resize(frame, (new_width, new_height))

    cv2.imshow(description, resized_frame)


class Detector:
    def __init__(self, minBlob, num_gaussians, canny_threshold_one, canny_threshold_two, canny_aperture_size, thresholding_threshold, dilating_matrix):
        self.backRemove = cv2.createBackgroundSubtractorKNN()
        self.minBlob = minBlob
        self.num_gaussians = num_gaussians
        self.canny_threshold_one = canny_threshold_one
        self.canny_threshold_two = canny_threshold_two
        self.canny_aperture_size = canny_aperture_size
        self.thresholding_threshold = thresholding_threshold
        self.dilating_matrix = dilating_matrix

    def Detect(self, frame):
        # display(frame, "original")

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # grayscale
        # display(gray, "grayscale")

        backSub = self.backRemove.apply(gray)  # background subs
        # display(backSub, "background substitution")

        img_blur = cv2.GaussianBlur(backSub, (self.num_gaussians, self.num_gaussians), 0)  # blur  # should be 3
        # display(img_blur, "blur")

        # THERE IS A DILATION STEP BELOW THAT WAS IMPLEMENTED BUT NOT USED
        # SOURCE: https://docs.opencv.org/3.4/db/df6/tutorial_erosion_dilatation.html
        # kernel = cv2.getStructuringElement(
        #     cv2.MORPH_ELLIPSE, (self.dilating_matrix, self.dilating_matrix))  # dilating (closing contours)
        # dilated = cv2.dilate(img_blur, kernel)
        # display(dilated, "dilated")
        
        dilated = img_blur  # if using dilation step, remove this

        edges = cv2.Canny(dilated, self.canny_threshold_one, self.canny_threshold_two, self.canny_aperture_size)  # edge detection
        # display(edges, "edges")

        _, thresh = cv2.threshold(edges, self.thresholding_threshold, 255, 0)  # thresholding
        # display(thresh, "thresh")

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # contours
        
        image_with_contours = frame.copy()

        centers = []  # center of mass of ant
        areas = []  # area of the center of mass of ant

        for cnt in contours:
            try:

                (x, y), radius = cv2.minEnclosingCircle(
                    cnt)  # draws circle around contour
                area = cv2.contourArea(cnt)  # gets area of contour
                centeroid, radius = (int(x), int(y)), int(radius)

                red = (0, 0, 255)  # bgr
                if (500 > area > self.minBlob):  # the area has to be at least minBlob  # 1000 is like a hard limit
                    # anything more than 500 is definitely NOT an ant and definitely isn't a merger of ants
                    cv2.circle(image_with_contours, centeroid,
                               radius, red, 1)
                    b = np.array([[x], [y]])
                    centers.append(np.round(b))
                    areas.append(area)
            except ZeroDivisionError:
                pass

            green = (0, 255, 0)  # bgr
            cv2.drawContours(image_with_contours, [cnt], 0, green, 1)
        # display(image_with_contours, "contours and circles")

        return centers, areas
