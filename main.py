import cv2
import datetime
import time
import os
import sys
from twilio.rest import Client

#Twilio Account Details
account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
from_number = os.environ.get("TWILIO_FROM_NUMBER")
client = Client(account_sid, auth_token)

# Load multiple cascades
upperbody_cascade = cv2.CascadeClassifier("harcascade/haarcascade_upperbody.xml")
lowerbody_cascade = cv2.CascadeClassifier("harcascade/haarcascade_lowerbody.xml")
fullbody_cascade = cv2.CascadeClassifier("harcascade/haarcascade_fullbody.xml")
frontalface_cascade = cv2.CascadeClassifier("harcascade/haarcascade_frontalface_default.xml")

# Get username and mobile number from command-line arguments
username = 'anonymous'
to_number = '' # Default empty
if len(sys.argv) > 1:
    username = sys.argv[1]
if len(sys.argv) > 2:
    to_number = sys.argv[2]

# Ensure uploads directory exists
if not os.path.exists('uploads'):
    os.makedirs('uploads')

base_dir = os.path.join('uploads', username)
screenshots_dir = os.path.join(base_dir, 'Screenshots')
videos_dir = os.path.join(base_dir, 'Videos')
os.makedirs(screenshots_dir, exist_ok=True)
os.makedirs(videos_dir, exist_ok=True)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 15)

duration = 20
screenshot_num = 1
sms_sent_count = 0
sms_limit = 3
screenshot_interval = 3  # Take a screenshot every 3 frames with detection
frame_counter = 0

fourcc = cv2.VideoWriter_fourcc(*'XVID')
video_name = os.path.join(videos_dir, f"video_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4v")
out = cv2.VideoWriter(video_name, fourcc, 10.0, (640, 480))

start_time = time.time()
end_time = start_time + duration

while time.time() < end_time:
    ret, image = cap.read()
    if not ret:
        break
    gray_scale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    detections = []
    # Detect with all four cascades
    for cascade in [upperbody_cascade, lowerbody_cascade, fullbody_cascade, frontalface_cascade]:
        bodies = cascade.detectMultiScale(gray_scale, 1.1, 3)
        for (x, y, w, h) in bodies:
            detections.append((x, y, w, h))
    frame_counter += 1
    if detections:
        # Pick the largest bounding box
        x, y, w, h = max(detections, key=lambda b: b[2]*b[3])
        cv2.rectangle(image, (x, y), (x+w, y+h), (255, 0, 0), 2)
        # Only take a screenshot every 'screenshot_interval' frames
        if frame_counter % screenshot_interval == 0:
            now = datetime.datetime.now()
            timestamp = now.strftime('%Y-%m-%d_%H-%M-%S')
            image_path = os.path.join(screenshots_dir, f'screenshot_{timestamp}.png')
            cv2.imwrite(image_path, image)
            screenshot_num += 1
            print(f'Screenshot {screenshot_num-1} taken')
            # Send SMS notification (limit to 3 per session)
            if sms_sent_count < sms_limit and to_number:
                try:
                    client.messages.create(
                        body="Movement detected!",
                        from_=from_number,
                        to=to_number,
                    )
                    sms_sent_count += 1
                except Exception as e:
                    print("Twilio error:", e)
    out.write(image)
    cv2.imshow("Frame", image)
    if cv2.waitKey(1) & 0xFF == ord("c"):
        break

cap.release()
out.release()
cv2.destroyAllWindows()