from dataAugmentationFunctions import process
import cv2
import copy
import numpy as np

test_data = {
    "framePath": "/home/adam/repos/Inzynierka/Sesje/_2019-05-15_19_54_01_449196/Obrazy/recording_2019-04-25 22:48:38.782457_frame_51.png",
    "augmentationCode": "0113",
    "expectedSize": (500, 500),
}


class CallbackFunctor:
    colorRed = (0, 0, 255)
    colorGreen = (0, 255, 0)
    colorBlue = (255, 0, 0)

    def __init__(self, img, color):
        self.color = self.getColor(color)

        self.img = img
        self.originalImg = copy.deepcopy(img)
        self.isCalled = False
        self.position = None

    def __call__(self, event, x, y, flags, userdata, *args, **kwargs):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.img = copy.deepcopy(self.originalImg)
            self.position = (x, y)
            cv2.drawMarker(self.img, self.position, self.color)
        if event == cv2.EVENT_LBUTTONDBLCLK:
            self.isCalled = True

    @classmethod
    def getColor(cls, color):
        if color == "red":
            return cls.colorRed
        elif color == "green":
            return cls.colorGreen
        else:
            return cls.colorBlue


def addPoint(img, color):
    callback = CallbackFunctor(img, color)
    while not cv2.waitKey(10) & callback.isCalled:
        cv2.imshow("test", callback.img)
        cv2.setMouseCallback("test", callback)
    return callback.position


def process_order(data):
    path = data["framePath"]
    img = cv2.imread(path)

    colors = "red", "green"
    positions = {color: addPoint(img, color) for color in colors}
    positions["blue"] = None

    imgs = process(path, positions, data["augmentationCode"])
    for imgDict in imgs:
        while not cv2.waitKey(10) & 0xFF == ord('w'):
            img = imgDict["img"]
            normalizedPositions = [el for el in imgDict["positions"].values() if el is not None]
            positions = zip(imgDict["positions"].keys(), (np.array(normalizedPositions) * img.shape[0:1]).astype(int))

            for color, position in positions:
                cv2.drawMarker(img, tuple(position), CallbackFunctor.getColor(color))

            cv2.imshow("test", img)


process_order(test_data)
