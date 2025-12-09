import numpy as np
import cv2
import glob
import yaml

# input/output
INPUT = 'input21'
OUTPUT = 'output21'
images = glob.glob(INPUT + '/*.jpg')
yamlname = OUTPUT + '/calibration_data_px.yaml'

# pattern SIZE
ROWS = 6  # internal corners only (chessboard rows - 1)
COLS = 9  # internal corners only (chessboard cols - 1)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((ROWS * COLS, 3), np.float32)
objp[:, :2] = np.mgrid[0:ROWS, 0:COLS].T.reshape(-1, 2)

# arrays to store object points and image points from all the input.
objpoints = []  # 3d point in real world space
imgpoints = []  # 2d points in image plane.

# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare window to display corners
cv2.namedWindow('Corners', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Corners', 800, 600)

for imgname in images:

    img = cv2.imread(imgname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, (ROWS, COLS), None)

    # If found, add object points, image points (after refining them)
    if ret:
        print('Adding {0} ...'.format(imgname))

        objpoints.append(objp)

        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners2)

        # Draw and display the corners
        img = cv2.drawChessboardCorners(img, (ROWS, COLS), corners2, ret)
        cv2.imshow('corners', img)
        cv2.waitKey(500)
    else:
        print('Bad image {0} !!!'.format(imgname))

cv2.destroyAllWindows()

print('Camera calibration...')
rms, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

print('RMS: {0}'.format(rms))
print('Camera matrix:')
print(mtx)
print('Distortion coefficients:')
print(dist)

# Write calibration results to YAML file
data = {'camera_matrix': mtx.tolist(), 'distortion_coefficients': dist.tolist(), 'rms': rms}
with open(yamlname, 'w') as f:
    yaml.dump(data, f)

print('Done!')
