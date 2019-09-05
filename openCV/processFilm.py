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
    frames_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    print(f"fps: {'%.2f' % fps}, frames: {'%.0f' % frames_count}")
    it = 0
    while 1:
        ret, frame = cap.read()
        if ret != False:
            fullFrameName = "{}_f{}.{}".format(filePrefix, it, imageSufix)
            fullPathToSave = os.path.join(pathToSave, fullFrameName).replace('\\', '/').replace(' ', '_')
            if not it % 2:
                print(f"{' ' * 50}\rProcessed: {'%.2f' % ((it/frames_count)*100)}%", end=f'\r', flush=True)
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
            print(f"{' ' * 50}\rProcessed: Done\n", flush=True)
            break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return frameInfo
