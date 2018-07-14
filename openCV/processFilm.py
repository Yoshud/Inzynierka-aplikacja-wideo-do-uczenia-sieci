import cv2
import time
import os
from pathlib import Path


def process(path, pathToSave, movieName, movieId):
    pathToCreate = Path(pathToSave)
    pathToCreate.mkdir(parents=True, exist_ok=True)
    frameInfo = []

    movieNameAndSufix = movieName.split('.')
    filePrefix = "{}_{}".format(movieNameAndSufix[0], movieId)
    movieSufix = movieNameAndSufix[1]
    imageSufix = "jpg"
    pathToSave = os.path.join(pathToSave, filePrefix).replace('\\', '/')
    start = time.time()
    cap = cv2.VideoCapture(path.replace('\\', '/'))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print("fps: {}".format(fps))
    it = 0
    frames = []

    while 1:
        ret, frame = cap.read()
        if ret != False:
            # frames.append(frame)
            fullPathToSave = "{}_f{}.{}".format(pathToSave, it, imageSufix)
            try:
                cv2.imwrite(fullPathToSave, frame)
                frameInfo.append({
                    "nr": it,
                    "date": time.time(),
                    "path": fullPathToSave,
                })
            except:
                print("??")

            it += 1
        else:
            break
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    print(len(frames))

    # for it, frame1 in enumerate(frames):
    #     # cv2.imwrite("{}_f{}.{}".format(pathToSave, it, fileSufix), frame1, cv2.IMWRITE_JPEG_RST_INTERVAL)
    #     fullPathToSave = "{}_f{}.{}".format(pathToSave, it, imageSufix)
    #     try:
    #         cv2.imwrite(fullPathToSave, frame1)
    #         frameInfo.append({
    #             "nr": it,
    #             "date": time.time(),
    #             "path": fullPathToSave,
    #         })
    #     except:
    #         print("??")
    #     if cv2.waitKey(10) & 0xFF == ord('q'):
    #         break
    print(time.time() - start)
    cap.release()
    cv2.destroyAllWindows()
    return frameInfo
