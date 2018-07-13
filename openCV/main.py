import cv2
import time
# import numpy as np
# import tensorflow as tf
# import pandas as pd
# import matplotlib.pyplot as plt
# from functools import reduce
# import os
# from scipy.misc import imread
# from PIL import Image
# from PIL import ImageDraw
# from PIL import ImageFont

def process(path, pathToSave):
    cap = cv2.VideoCapture(path.replace('\\', '/'))

    fps = cap.get(cv2.CAP_PROP_FPS)
    print("fps: {}".format(fps))
    ret, frame = cap.read()
    fps = 1
    it = 0
    frames = []

    while 1:
        ret, frame = cap.read()
        if ret != False:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frames.append(frame)
            it+=1
        else:
            break
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    print (len(frames))
    start = time.time()
    for frame1 in frames:
        start_time = time.time()
        cv2.imshow("adam", frame1)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break
        sleep_time = 1 / fps - (time.time() - start_time)
        sleep_time = sleep_time if sleep_time > 0.0 else 0.0
        time.sleep(sleep_time)
        print("{} fps".format(1/(time.time() - start_time)))
    print(time.time() - start)
    cap.release()
    cv2.destroyAllWindows()
