from openCV.dataAugmentationFunctions import process
import cv2
import copy

test_data = {
    "framePath": "/home/adam/repos/Inzynierka/Sesje/testDodawania_2019-05-01_22_33_46_856457/Obrazy/recording_2019-04-25 22:41:26.783159_frame_2230.png",
    "augmentationCode": "0113",
    "expectedSize": (500, 500),
}


class CallbackFunctor:
    colorRed = (0, 0, 255)

    def __init__(self, img):
        self.img = img
        self.originalImg = copy.deepcopy(img)
        self.isCalled = False
        self.position = None

    def __call__(self, event, x, y, flags, userdata, *args, **kwargs):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.img = copy.deepcopy(self.originalImg)
            self.position = (x, y)
            cv2.drawMarker(self.img, self.position, self.colorRed)
        if event == cv2.EVENT_LBUTTONDBLCLK:
            self.isCalled = True


def process_order(data):
    path = data["framePath"]
    img = cv2.imread(path)

    callback = CallbackFunctor(img)
    while not cv2.waitKey(10) & callback.isCalled:
        cv2.imshow("test", callback.img)
        cv2.setMouseCallback("test", callback)

    imgs = process(path, callback.position, data["augmentationCode"], data["expectedSize"])
    for imgDict in imgs:
        while not cv2.waitKey(10) & 0xFF == ord('w'):
            img = imgDict["img"]
            position = int(round(imgDict["position"][0])), int(round(imgDict["position"][1]))
            cv2.drawMarker(img, position, (0, 0, 255))
            cv2.imshow("test", img)


process_order(test_data)
