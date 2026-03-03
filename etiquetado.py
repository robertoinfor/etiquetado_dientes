import cv2
import numpy as np
import _tkinter as tk

drawing = False
ix, iy = -1, -1

def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, img

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            temp = img.copy()
            cv2.rectangle(temp, (ix, iy), (x, y), (0,255,0), 2)
            cv2.imshow("Etiquetador", temp)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        cv2.rectangle(img, (ix, iy), (x, y), (0,255,0), 2)

img = cv2.imread("imagen.jpg")
cv2.namedWindow("Etiquetador")
cv2.setMouseCallback("Etiquetador", draw_rectangle)

while True:
    cv2.imshow("Etiquetador", img)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cv2.destroyAllWindows()
