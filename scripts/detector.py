# Borrowed Heavily From Srini Ananthakrishnan's Multi Object Tracking Model
# https://github.com/srianant/kalman_filter_multi_object_tracking

import numpy as np
import cv2

dis_vid = True
toDisplay = False


def display(frame, desc, final=False):

    try:
        height, width = frame.shape
    except:
        height, width, _ = frame.shape

    dis_vid = False  # use True only when local

    scaler = 4

    new_width = width * scaler
    new_height = height * scaler
    resized_frame = cv2.resize(frame, (new_width, new_height))

    if dis_vid or final:
        cv2.imshow(desc, resized_frame)


class Detector(object):
    def __init__(self, minBlob, num_gaussians, canny_threshold_one, canny_threshold_two, canny_aperture_size, thresholding_threshold, dilating_matrix, debug):
        self.backRemove = cv2.createBackgroundSubtractorKNN()
        self.minBlob = minBlob
        self.num_gaussians = num_gaussians
        self.canny_threshold_one = canny_threshold_one
        self.canny_threshold_two = canny_threshold_two
        self.canny_aperture_size = canny_aperture_size
        self.thresholding_threshold = thresholding_threshold
        self.dilating_matrix = dilating_matrix

    def Detect(self, frame):
        display(frame, "original")

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # grayscale
        display(gray, "grayscale")

        backSub = self.backRemove.apply(gray)  # background subs
        display(backSub, "background substitution")

        img_blur = cv2.GaussianBlur(
            backSub, (self.num_gaussians, self.num_gaussians), 0)  # blur  # should be 3
        display(img_blur, "blur")

        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (self.dilating_matrix, self.dilating_matrix))  # dilating (closing contours)
        dilated = cv2.dilate(img_blur, kernel)
        display(dilated, "dilated")

        edges = cv2.Canny(dilated, self.canny_threshold_one,
                          self.canny_threshold_two, self.canny_aperture_size)  # edge detection
        display(edges, "edges")

        _, thresh = cv2.threshold(
            edges, self.thresholding_threshold, 255, 0)  # thresholding
        display(thresh, "thresh")

        contours, _ = cv2.findContours(dilated,
                                       cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)  # contours
        
        image_with_contours = frame.copy()

        centers = []  # center of mass of ant

        for cnt in contours:
            try:

                (x, y), radius = cv2.minEnclosingCircle(
                    cnt)  # draws circle around contour
                area = cv2.contourArea(cnt)  # gets area of contour
                centeroid, radius = (int(x), int(y)), int(radius)

                red = (0, 0, 255)  # bgr
                if (area > self.minBlob):  # the area has to be at least minBlob
                    cv2.circle(image_with_contours, centeroid,
                               radius, red, 1)
                    b = np.array([[x], [y]])
                    centers.append(np.round(b))
            except ZeroDivisionError:
                pass

            green = (0, 255, 0)  # bgr
            cv2.drawContours(image_with_contours, [cnt], 0, green, 1)
        display(image_with_contours, "contours and circles")

        return centers
