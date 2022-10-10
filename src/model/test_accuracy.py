import csv
import os
import cv2
import imutils
import numpy as np
import argparse
import shutil

CLASSES = [
    "background",
    "aeroplane",
    "bicycle",
    "bird",
    "boat",
    "bottle",
    "bus",
    "car",
    "cat",
    "chair",
    "cow",
    "diningtable",
    "dog",
    "horse",
    "motorbike",
    "person",
    "pottedplant",
    "sheep",
    "sofa",
    "train",
    "tvmonitor",
]
COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

ap = argparse.ArgumentParser()
ap.add_argument(
    "-p", "--prototxt", required=True, help="path to Caffe 'deploy' prototxt file"
)
ap.add_argument("-m", "--model", required=True, help="path to Caffe pre-trained model")
args = vars(ap.parse_args())
CONFIDENCE = 0.6

net = cv2.dnn.readNetFromCaffe(args["prototxt"], args["model"])


def getNumberOfPeople(frame):
    frame = imutils.resize(frame, width=400)
    # grab the frame dimensions and convert it to a blob
    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(
        cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5
    )
    # pass the blob through the network and obtain the detections and
    # predictions
    net.setInput(blob)
    detections = net.forward()
    # loop over the detections
    people_count = 0
    for i in np.arange(0, detections.shape[2]):
        # extract the confidence (i.e., probability) associated with
        # the prediction
        confidence = detections[0, 0, i, 2]
        # filter out weak detections by ensuring the `confidence` is
        # greater than the minimum confidence
        if confidence > CONFIDENCE:
            # extract the index of the class label from the
            # `detections`, then compute the (x, y)-coordinates of
            # the bounding box for the object
            idx = int(detections[0, 0, i, 1])
            if CLASSES[idx] == "person":
                people_count += 1
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")
            # draw the prediction on the frame
            label = "{}: {:.2f}%".format(CLASSES[idx], confidence * 100)
            cv2.rectangle(frame, (startX, startY), (endX, endY), COLORS[idx], 2)
            y = startY - 15 if startY - 15 > 15 else startY + 15
            cv2.putText(
                frame, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2
            )
    return (people_count, frame)


result = []

IMAGES_PREFIX = "images/"
OUTPUT_PREFIX = "output/"
PASSED_PREFIX = OUTPUT_PREFIX + "passed/"
FAILED_PREFIX = OUTPUT_PREFIX + "failed/"
if os.path.exists(OUTPUT_PREFIX):
    shutil.rmtree(OUTPUT_PREFIX)
os.makedirs(PASSED_PREFIX, exist_ok=True)
os.makedirs(FAILED_PREFIX, exist_ok=True)

total_error = 0

with open("dataset.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        filename = row["filename"]
        expected = int(row["count"])
        frame = cv2.imread(IMAGES_PREFIX + filename)
        actual, frame = getNumberOfPeople(frame)

        os.makedirs(OUTPUT_PREFIX, exist_ok=True)
        prefix = PASSED_PREFIX if actual == expected else FAILED_PREFIX
        if not cv2.imwrite(
            prefix + filename,
            frame,
        ):
            print("failed to save frame", prefix + filename)
        else:
            print("saved frame", prefix + filename)

        row["result"] = "PASS" if actual == expected else "FAIL"
        row["actual"] = actual
        result.append(row)

        total_error += (expected - actual) * (expected - actual)

with open("result.csv", "w") as f:
    fieldnames = ["filename", "count", "result", "actual"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(result)

rmse = np.sqrt(total_error / len(result))
print("RMSE:", rmse)
