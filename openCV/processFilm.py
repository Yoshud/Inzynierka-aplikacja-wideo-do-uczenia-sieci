import cv2
import os
from pathlib import Path


def process(path, pathToSave, movieName, movieId):
    pathToCreate = Path(pathToSave)
    pathToCreate.mkdir(parents=True, exist_ok=True)
    frameInfo = []

    movieNameAndSufix = movieName.split('.')
    filePrefix = "{}_{}".format(movieNameAndSufix[0], movieId)
    imageSufix = "png"
    cap = cv2.VideoCapture(path.replace('\\', '/'))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print("fps: {}".format(fps))
    it = 0
    while 1:
        ret, frame = cap.read()
        if ret != False:
            fullFrameName = "{}_f{}.{}".format(filePrefix, it, imageSufix)
            fullPathToSave = os.path.join(pathToSave, fullFrameName).replace('\\', '/').replace(' ', '_')
            try:
                cv2.imwrite(fullPathToSave, frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])
                frameInfo.append({
                    "nr": it,
                    "name": fullFrameName,
                })
            except:
                print("??")

            it += 1
        else:
            break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return frameInfo
