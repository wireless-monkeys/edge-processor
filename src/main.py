# import the necessary packages
from imutils.video import VideoStream
import numpy as np
import argparse
import imutils
import time
import cv2
import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from led import set_led_output, cleanup
from stubs import edge_service_pb2_grpc, edge_service_pb2

channel = grpc.insecure_channel("wm.suphon.dev:4000")
stub = edge_service_pb2_grpc.EdgeServiceStub(channel)

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument(
    "-p", "--prototxt", required=True, help="path to Caffe 'deploy' prototxt file"
)
ap.add_argument("-m", "--model", required=True, help="path to Caffe pre-trained model")
ap.add_argument(
    "-c",
    "--confidence",
    type=float,
    default=0.6,
    help="minimum probability to filter weak detections",
)
ap.add_argument(
    "-s", "--show", action="store_true", help="path to Caffe pre-trained model"
)
ap.add_argument(
    "-co",
    "--cutoff",
    type=float,
    default=60,
    help="number of seconds before turning off the led",
)
args = vars(ap.parse_args())

# initialize the list of class labels MobileNet SSD was trained to
# detect, then generate a set of bounding box colors for each class
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
# COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))
COLOR = (255, 0, 0)

# load our serialized model from disk
print("[INFO] loading model...")
net = cv2.dnn.readNetFromCaffe(args["prototxt"], args["model"])
# initialize the video stream, allow the cammera sensor to warmup
print("[INFO] starting video stream...")
vs = VideoStream(src=0).start()
time.sleep(1.0)


def getImageAndNumberOfPeople():
    # grab the frame from the threaded video stream and resize it
    # to have a maximum width of 400 pixels
    frame = vs.read()
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
        if confidence > args["confidence"]:
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
                cv2.rectangle(frame, (startX, startY), (endX, endY), COLOR, 2)
                y = startY - 15 if startY - 15 > 15 else startY + 15
                cv2.putText(
                    frame,
                    label,
                    (startX, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    COLOR,
                    2,
                )
    return (people_count, frame)


last_timestamp_with_people = 0

try:
    while True:
        (people_count, frame) = getImageAndNumberOfPeople()

        # Create timestamp
        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 1e9)
        t = Timestamp(seconds=seconds, nanos=nanos)

        # Send data to server
        obj = edge_service_pb2.SetDataRequest(
            timestamp=t,
            number_of_people=people_count,
            camera_image=cv2.imencode(".jpg", frame)[1].tobytes(),
        )
        stub.SetData(obj)

        if people_count > 0:
            last_timestamp_with_people = time.time()
            set_led_output(True)
        elif time.time() - last_timestamp_with_people > args["cutoff"]:
            set_led_output(False)
        else:
            set_led_output(True)

        # time.sleep(0.5)
        # show the output frame
        if args["show"]:
            cv2.imshow("Frame", frame)

            key = cv2.waitKey(1) & 0xFF
            # if the `q` key was pressed, break from the loop
            if key == ord("q"):
                # do a bit of cleanup
                cv2.destroyAllWindows()
                vs.stop()
except KeyboardInterrupt:
    cleanup()
