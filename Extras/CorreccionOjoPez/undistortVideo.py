import numpy as np
import cv2
import yaml
import glob
import os
import matplotlib.pyplot as plt

INPUT = 'input21'
OUTPUT = 'output21'
images = glob.glob(INPUT + '/*.jpg')
yamlname = OUTPUT + '/calibration_data_px.yaml'


def compare_images(imageA, imageB, title):
    # setup the figure
    fig = plt.figure(title)

    # show first image
    ax = fig.add_subplot(1, 2, 1)
    plt.imshow(imageA, cmap=plt.cm.gray)
    plt.axis("off")

    # show the second image
    ax = fig.add_subplot(1, 2, 2)
    plt.imshow(imageB, cmap=plt.cm.gray)
    plt.axis("off")

    # show the images
    plt.show()


with open(yamlname) as f:
    data = yaml.safe_load(f)

cam_matrix = np.array(data['camera_matrix'])
dist_coefs = np.array(data['distortion_coefficients'])

print(cam_matrix)
print(dist_coefs)

for imgname in images:
    print('Undistorting {0} ...'.format(imgname))

    img = cv2.imread(imgname)
    h, w = img.shape[:2]

    # With alpha=1 all source pixels are undistorted, which can lead to a non-rectangular image region.
    # Because the image has to be rectangular in memory, the gaps are padded with black pixels.
    # Setting alpha=1 effectively increases the focal length to have a rectangular undistorted image
    # where all pixels correspond to a pixel in the original. You lose data from the periphery,
    # but you don't have any padded pixels without valid data

    new_cam_mtx, roi = cv2.getOptimalNewCameraMatrix(cam_matrix, dist_coefs, (w, h), 1, (w, h))

    u_img = cv2.undistort(img, cam_matrix, dist_coefs, None, new_cam_mtx)

    name, ext = os.path.splitext(os.path.basename(imgname))


    cv2.imwrite(os.path.join(OUTPUT, name + '_und1' + ext), u_img)

    # compare_images(img, u_img, "Undistort")

    x, y, w, h = roi
    # crop and save the undistorted image
    dst = u_img[y:y + h, x:x + w]
    cv2.imwrite(os.path.join(OUTPUT, name + '_und1_crop' + ext), dst)
    # Or draw roi on image an save
    cv2.rectangle(u_img, (x, y), (x + w, y + h), (0, 255, 0), 1)
    cv2.imwrite(os.path.join(OUTPUT, name + '_und1_roi' + ext), u_img)

print('ok')
