import numpy as np
import cv2

debug = False  # displays video
toDisplay = False

# displays video. makes it bigger so you can see it
def display(frame, desc, final=False):

    try:
        height, width = frame.shape
    except:
        height, width, _ = frame.shape

    new_width = width * 4
    new_height = height * 4
    resized_frame = cv2.resize(frame, (new_width, new_height))

    if debug or final:
        cv2.imshow(desc, resized_frame)


class Detector(object):

    def __init__(self, minBlob, num_gaussians):
        self.backRemove = cv2.createBackgroundSubtractorKNN()
        self.minBlob = minBlob
        self.num_gaussians = num_gaussians

    def Detect(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # grayscale
        display(gray, "grayscale")

        backSub = self.backRemove.apply(gray)  # background subs
        display(backSub, "background substitution")

        img_blur = cv2.GaussianBlur(
            backSub, (self.num_gaussians, self.num_gaussians), 0)  # blur  # should be 3
        display(img_blur, "blur")

        edges = cv2.Canny(img_blur, 50, 200, 3)  # edge detection
        display(edges, "edges")

        ret, thresh = cv2.threshold(edges, 127, 255, 0)  # thresholding
        display(thresh, "thresh")

        contours, hierarchy = cv2.findContours(thresh,
                                               cv2.RETR_EXTERNAL,
                                               cv2.CHAIN_APPROX_SIMPLE)  # contours
        image_with_contours = frame.copy()

        centers = []  # center of mass of ant
        area_thresh = self.minBlob  # area of contour  # should be 0

        for cnt in contours:
            try:
                # makes more enclosures
                epsilon = 0.05 * cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, epsilon, True)

                (x, y), radius = cv2.minEnclosingCircle(approx)
                area = cv2.contourArea(approx)
                centeroid = (int(x), int(y))
                radius = int(radius)
                if (area > area_thresh):
                    cv2.circle(image_with_contours, centeroid,
                               radius, (0, 0, 255), 1)
                    b = np.array([[x], [y]])
                    centers.append(np.round(b))
            except ZeroDivisionError:
                pass
            cv2.drawContours(image_with_contours, [approx], 0, (0, 255, 0), 1)
        display(image_with_contours, "contours and circles")

        return centers
