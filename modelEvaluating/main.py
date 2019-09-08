import cv2
from pathlib import Path
from ModelML.SimpleSMAppTracingModel import SimpleSMAppTracingModel as Model
import numpy as np


def getPositions(result, color):
    positions = (result[color] * np.array(model.input_size))
    return tuple(int(el) for el in positions[0])


session_path = Path("/media/adam/Dane/Dane/Sesje/E2E_v1_2019-06-03_22_07_47_365552")
data_augmentation_folder_path = session_path.joinpath("dataAugmentation_2019-06-04_21_01_17_013405")

image_path = data_augmentation_folder_path.joinpath("recording_2019-06-02 "
                                                    "13:23:59.848442_frame_7_O_crop_464_352_140408406453704.png")
model_path = session_path.joinpath("Modele/model_2")

img = cv2.imread(str(image_path))
model = Model.load(model_path)

result = model.predict(img)
result2 = model.predict(img)
result3 = model.predict(img)

colorRed = (0, 0, 255)
colorYellow = (255, 255, 0)
colorPurple = (255, 0, 255)
colorBlue = (0, 255, 0)


cv2.drawMarker(img, getPositions(result, "Czerwony"), colorRed)
cv2.drawMarker(img, getPositions(result, "Zolty"), colorYellow)
cv2.drawMarker(img, getPositions(result, "Fioletowy"), colorPurple)
cv2.drawMarker(img, getPositions(result, "Niebieski"), colorBlue)

while not cv2.waitKey(10) & 0xFF == ord('w'):
    cv2.imshow("Result", img)

print(result)
