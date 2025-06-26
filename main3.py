import cv2
import tkinter as tk
from tkinter import filedialog
from twilio.rest import Client
import datetime
import sys
import os

# Ensure uploads directory exists
if not os.path.exists('uploads'):
    os.makedirs('uploads')

# Initialize Twilio client
account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
from_number = os.environ.get("TWILIO_FROM_NUMBER")
client = Client(account_sid, auth_token)

# Load multiple cascades
upperbody_cascade = cv2.CascadeClassifier("harcascade/haarcascade_upperbody.xml")
lowerbody_cascade = cv2.CascadeClassifier("harcascade/haarcascade_lowerbody.xml")
fullbody_cascade = cv2.CascadeClassifier("harcascade/haarcascade_fullbody.xml")
frontalface_cascade = cv2.CascadeClassifier("harcascade/haarcascade_frontalface_default.xml")

# This script is not intended to run a GUI directly anymore when called from the web app.
# The following GUI code is now only for manual fallback.
def setup_gui():
    root = tk.Tk()
    root.title('Motion Detection')
    root.geometry('300x150')

    label = tk.Label(root, text='Select a video file')
    label.pack(pady=10)

    def select_file():
        file_path = filedialog.askopenfilename(filetypes=[('Video Files', '*.mp4v;*.mp4;*.avi;*.mpg;*.mpeg;*.mov;*.wmv;*.flv')])
        if file_path:
            motion_detection(file_path)

    button = tk.Button(root, text='Select File', command=select_file)
    button.pack(pady=10)
    root.mainloop()

def motion_detection(file_path, username='anonymous', to_number=''):
    cascPath = "harcascade\\haarcascade_frontalface_default.xml"  # Not used anymore
    cap = cv2.VideoCapture(file_path)

    # Prepare user-specific directories
    base_dir = os.path.join('uploads', username)
    screenshots_dir = os.path.join(base_dir, 'Screenshots')
    videos_dir = os.path.join(base_dir, 'Videos')
    os.makedirs(screenshots_dir, exist_ok=True)
    os.makedirs(videos_dir, exist_ok=True)

    # Prepare video writer
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    video_name = os.path.join(videos_dir, f"video_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4v")
    out = cv2.VideoWriter(video_name, fourcc, 10.0, (int(cap.get(3)), int(cap.get(4))))

    frame_count = 120
    buffer_size = 10
    buffer = []
    sms_sent_count = 0
    sms_limit = 3
    screenshot_interval = 3
    frame_counter = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detections = []
        for cascade in [upperbody_cascade, lowerbody_cascade, fullbody_cascade, frontalface_cascade]:
            bodies = cascade.detectMultiScale(gray, 1.1, 3)
            for (x, y, w, h) in bodies:
                detections.append((x, y, w, h))
        frame_counter += 1
        if detections:
            # Pick the largest bounding box
            x, y, w, h = max(detections, key=lambda b: b[2]*b[3])
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            if frame_counter % screenshot_interval == 0:
                now = datetime.datetime.now()
                timestamp = now.strftime('%Y-%m-%d_%H-%M-%S')
                image_path = os.path.join(screenshots_dir, f'screenshot_{timestamp}.png')
                cv2.imwrite(image_path, frame)
                # Send SMS notification (limit to 3 per session)
                if sms_sent_count < sms_limit and to_number:
                    try:
                        message = client.messages.create(
                            body='Motion detected!',
                            from_=from_number,
                            to=to_number,
                        )
                        sms_sent_count += 1
                    except Exception as e:
                        print("Twilio error:", e)
        out.write(frame)
        # We don't need to show the window when running from web app
        # cv2.imshow('Motion Detection', frame)
        if cv2.waitKey(1) == ord('c'):
            break
        frame_count += 1
    cap.release()
    out.release()
    cv2.destroyAllWindows()

# Run GUI
if __name__ == '__main__':
    # Updated argument handling
    if len(sys.argv) > 3:
        file_path = sys.argv[1]
        username = sys.argv[2]
        to_number = sys.argv[3]
        motion_detection(file_path, username, to_number)
    elif len(sys.argv) > 2:
        file_path = sys.argv[1]
        username = sys.argv[2]
        motion_detection(file_path, username)
    elif len(sys.argv) > 1:
        file_path = sys.argv[1]
        motion_detection(file_path)
    else:
        # GUI fallback for manual testing
        setup_gui()
