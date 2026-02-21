# YouTube Song Mashup Service

A modernized, high-performance Python application that generates a custom audio mashup from any YouTube artist search. The application is available as both a **Command Line Interface (CLI) tool** and a **responsive Web Service** with non-blocking execution, real-time progress updates, and secure email delivery.

---

## Features

- **Double Entry points**: Works seamlessly via CLI (`102303945.py`) or Web interface (`app.py`).
- **Non-Blocking Background Threads**: Web server remains completely responsive while processing heavy mashups.
- **Real-Time Progress Tracking**: The web interface uses AJAX polling to show progress percentages and live stage descriptions (e.g. *Downloading video 3 of 11...*, *Slicing clips...*).
- **Direct FFmpeg Audio Extraction**: Replaced slow and heavy MoviePy with native FFmpeg subprocess operations, leading to faster execution and lower system footprint.
- **Unoptimized Video Bypass**: Downloads only the audio streams (`bestaudio`) directly, saving up to 10x network bandwidth and disk usage.
- **Duration Filter**: Automatically filters out compilation video mixes (longer than 10 minutes) so only actual songs are downloaded.
- **Unicode Safe Filenames**: Replaces special symbols and characters in filenames with clean ASCII tags to prevent OS file mapping and log encoding errors.
- **Dynamic Temporary Workspaces**: Generates thread-safe request directories via Python `tempfile` and auto-destructs them on completion (no temp files accumulate).
- **Production Ready**: Fully prepared for Gunicorn, Docker containerization, and Waitress.

---

## Project Architecture

```text
Mashup_Project/
├── 102303945.py           # CLI Entry Point
├── app.py                 # Flask App Entry Point
├── routes.py              # Routing, Controller & Background Job Layer
├── config.py              # Configuration & Environment Handler
├── utils.py               # Sanitization, Email validation & FFmpeg checks
├── services/
│   ├── youtube_service.py # Audio downloading & searching (yt-dlp)
│   ├── audio_service.py   # Audio clipping, merging, and archiving (pydub)
│   └── email_service.py   # SMTP secure sending (smtplib)
├── templates/
│   └── index.html         # Responsive glassmorphic frontend UI
├── static/
│   ├── style.css          # CSS styles, glassmorphism, animations
│   └── script.js          # AJAX submit handler and progress tracker
├── .env.example           # Environment template file
├── requirements.txt       # Dependency versions
├── Dockerfile             # Container blueprint
├── docker-compose.yml     # Local orchestration
└── Procfile               # Cloud deployment (Heroku)
```

---

## Installation

### Prerequisites: Install FFmpeg
The audio processor requires FFmpeg and FFprobe installed on your system PATH.

#### 1. Windows
- **Via winget (Recommended)**: Open terminal as Administrator and run:
  ```powershell
  winget install Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
  ```
  Restart your terminal/shell to apply the PATH variables.
- **Manual**: Download the full build zip from [Gyan.dev](https://www.gyan.dev/ffmpeg/builds/), extract it, and add the `/bin` folder to your system Environment Variables (`PATH`).

#### 2. macOS
Install via Homebrew:
```bash
brew install ffmpeg
```

#### 3. Linux
Install via apt/yum:
```bash
sudo apt update && sudo apt install -y ffmpeg
# or
sudo yum install -y ffmpeg
```

---

### Setup Application

1. **Clone or navigate into the project directory**:
   ```bash
   cd Mashup_Project
   ```

2. **Create a virtual environment (Recommended)**:
   ```bash
   python -m venv venv
   
   # Activate on Windows:
   .\venv\Scripts\activate
   
   # Activate on macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**:
   Copy the example environment template and configure your credentials:
   ```bash
   cp .env.example .env
   ```
   Open the `.env` file and set:
   - `SENDER_EMAIL`: The GMail (or other provider) address that will send the mashups.
   - `SENDER_APP_PASSWORD`: The 16-character Google App Password (do not use your account's regular password).

---

## Running Locally

### 1. CLI Usage
Run the script passing the artist name, number of videos to download (>10), segment crop duration (>20 seconds), and the output path:
```bash
python 102303945.py "Arijit Singh" 11 25 output_mashup.mp3
```

### 2. Web Service
Start the Flask application:
```bash
python app.py
```
Open `http://127.0.0.1:5000` in your web browser. Fill out the glassmorphic form and watch the progress updates!

---

## Docker Deployment

To build and run the application in a completely isolated environment (preconfigured with Python 3.11, FFmpeg, and dependencies):

1. **Build the container**:
   ```bash
   docker-compose build
   ```
2. **Start the service**:
   ```bash
   docker-compose up
   ```
The web application will be accessible at `http://localhost:5000`.

---

## Troubleshooting

- **Google App Passwords**: Since May 2022, Google does not allow "Less Secure Apps" to login using your primary password. You must go to your Google Account Settings -> Security -> Enable 2-Step Verification -> App Passwords, generate a new password for "Mail", and paste the 16-digit code in the `.env` file.
- **YouTube Bot Block (Sign in to confirm you're not a bot)**: YouTube rate-limits anonymous command-line downloads. We have set up retries, timeout parameters, and restricted searches, but if YouTube still blocks your IP, place a fresh export of your browser cookies into a file named `cookies.txt` in the project root. The app will detect and use it automatically.
- **FFmpeg Not Found**: Ensure you restarted your terminal after installing FFmpeg. Run `ffmpeg -version` to verify it works outside the python script.
