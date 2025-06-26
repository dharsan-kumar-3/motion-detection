# Motion Detection & Security Notify System

A modern, web-based motion detection and security notification system built with Python, Flask, OpenCV, and Twilio. Detects motion in real-time or from uploaded videos, sends SMS alerts, and provides a secure dashboard for reviewing and downloading session data.

---

## Features
- **User Registration & Login** (with email/mobile verification)
- **Real-Time Motion Detection** via webcam
- **Video File Analysis** for motion events
- **Automatic Video & Screenshot Capture**
- **Instant SMS Alerts** (Twilio integration)
- **Personalized Dashboard** for reviewing and downloading session data
- **Professional, responsive UI**

---

## Quick Start

### 1. Clone the Repository
```bash
 git clone https://github.com/yourusername/motion-detection-app.git
 cd motion-detection-app
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
Create a `.env` file or set these in your hosting dashboard:
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_NUMBER`

Or update them directly in `main.py` and `main3.py` (not recommended for production).

### 4. Run Locally
```bash
python app.py
```
Visit [http://localhost:5000](http://localhost:5000)

---

## Deployment

### Render / Railway / Heroku
- Ensure you have `requirements.txt`, `Procfile`, and `runtime.txt` in your repo.
- Push your code to GitHub.
- Connect your repo to your chosen platform and deploy.
- Set your environment variables in the platform dashboard.

---

## Folder Structure
```
Motion_Detection/
├── app.py                # Flask backend
├── main.py               # Real-time webcam detection
├── main3.py              # Video file detection
├── templates/            # HTML templates
├── static/               # CSS, JS, images
├── harcascade/           # Haar cascade XMLs
├── uploads/              # User session data
├── users.xlsx            # User database
├── requirements.txt
├── Procfile
├── runtime.txt
└── README.md
```

---

## Credits
- Built with [Flask](https://flask.palletsprojects.com/), [OpenCV](https://opencv.org/), [Twilio](https://www.twilio.com/), and [pandas](https://pandas.pydata.org/).

---

## License
MIT License 