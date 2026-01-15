Here is the **FULL, CLEAN, FINAL README.md** that you can **directly copy–paste** into your project.
It already includes **everything they asked for**: setup, running locally, RTSP (including phone camera), API docs, and user guide.

---

# RTSP Livestream Overlay Web Application

A professional **RTSP Livestream Overlay Web Application** that plays live RTSP streams (converted to HLS using FFmpeg) and allows **real-time overlay creation, drag-and-drop positioning, resizing, editing, and database persistence** using a modern React frontend and a Flask backend.

---

## 🎯 Features

* ✅ RTSP livestream playback with automatic RTSP → HLS conversion
* ✅ Tested using **mobile phone camera as RTSP source**
* ✅ Real-time text and image overlays
* ✅ Drag, resize, edit overlays directly on live video
* ✅ Full CRUD APIs for overlay management
* ✅ MongoDB persistence for overlays
* ✅ Professional React UI
* ✅ Backend health checks and error handling

---

## 📁 Project Structure

```
Assignment/
├── backend/
│   ├── app.py                 # Flask backend
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example           # Environment template
│   └── streams/               # HLS output directory (auto-created)
│
├── frontend/
│   ├── src/
│   │   ├── App.js              # Main React app
│   │   ├── VideoPlayer.js      # HLS video player
│   │   ├── OverlayManager.js   # Overlay CRUD UI
│   │   └── styles.css          # Styling
│   ├── package.json
│   └── public/
│
└── README.md
```

---

## 🔧 Prerequisites

Ensure the following are installed:

* **Python 3.8+**
* **Node.js 16+**
* **MongoDB**
* **FFmpeg (Required)**

---

## 🎥 Installing FFmpeg (Windows)

1. Download FFmpeg: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extract to:

   ```
   C:\ffmpeg
   ```
3. Add to **System PATH**:

   ```
   C:\ffmpeg\bin
   ```
4. Verify installation:

   ```bash
   ffmpeg -version
   ```

---

## 🚀 Running the Application Locally

### ▶ Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
python app.py
```

Backend runs at:

```
http://localhost:5000
```

---

### ▶ Frontend Setup

```bash
cd frontend
npm install
npm start
```

Frontend runs at:

```
http://localhost:3000
```

---

## 📖 How to Use the Application

---

### 1️⃣ Providing or Changing the RTSP URL

1. Enter a valid **RTSP URL** in the input field
2. Click **Start Stream**
3. Wait 5–10 seconds for FFmpeg to convert the stream
4. Video playback starts automatically

---

### 🔹 RTSP URL Examples

#### Public Test Streams

```
rtsp://rtsp.stream/pattern
rtsp://rtsp.stream/people
rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4
```

---

### 🔹 Using Phone Camera as RTSP Source (Tested)

This project was tested using a **mobile phone camera** as an RTSP source.

**Steps:**

1. Install **RTSP Camera – Live Stream** app on your phone
2. Start streaming in the app
3. The app provides an RTSP URL like:

   ```
   rtsp://192.168.x.x:8554/live
   ```
4. Ensure phone and laptop are on the **same Wi-Fi**
5. Paste the RTSP URL into the application and start the stream

---

## 🎬 Livestream Playback

* RTSP streams are converted to **HLS format**
* HLS playlist generated:

  ```
  /streams/<stream_id>/index.m3u8
  ```
* Video playback uses **hls.js** in the browser

---

## 🧩 Overlay Management – User Guide

### ➕ Add Overlay

* Choose **Text** or **Image**
* Enter text or image URL
* Click **Add Overlay**

### ✋ Move Overlay

* Click and drag overlay on the video

### 🔄 Resize Overlay

* Drag overlay corners to resize

### ✏ Edit Overlay

* Click edit icon and update content

### 🗑 Delete Overlay

* Click delete icon to remove overlay

✔ All overlay changes are saved automatically in MongoDB

---

## 🔌 API Documentation

### Base URL

```
http://localhost:5000/api
```

---

### 🔹 Health Check

```http
GET /api/health
```

**Response**

```json
{
  "status": "healthy",
  "mongodb": "connected",
  "ffmpeg": "available",
  "active_streams": 1
}
```

---

### 🔹 Start Stream

```http
POST /api/stream
```

```json
{
  "rtsp_url": "rtsp://rtsp.stream/pattern"
}
```

---

### 🔹 Stop Stream

```http
POST /api/stream/{stream_id}/stop
```

---

### 🔹 Create Overlay

```http
POST /api/overlays
```

```json
{
  "type": "text",
  "content": "LIVE",
  "x": 50,
  "y": 50,
  "width": 150,
  "height": 60,
  "stream_id": "default"
}
```

---

### 🔹 Get All Overlays

```http
GET /api/overlays?stream_id=default
```

---

### 🔹 Update Overlay

```http
PUT /api/overlays/{overlay_id}
```

```json
{
  "x": 120,
  "y": 200,
  "content": "Updated Text"
}
```

---

### 🔹 Delete Overlay

```http
DELETE /api/overlays/{overlay_id}
```

---

## 🧪 Testing with cURL

### Health Check

```bash
curl http://localhost:5000/api/health
```

### Start Stream

```bash
curl -X POST http://localhost:5000/api/stream \
-H "Content-Type: application/json" \
-d "{\"rtsp_url\":\"rtsp://rtsp.stream/pattern\"}"
```

---

## 🛠 Troubleshooting

### Video Not Playing

* Verify RTSP URL works in VLC
* Ensure FFmpeg is installed
* Wait a few seconds for HLS generation

### 404 on index.m3u8

* Ensure backend is running
* Ensure FFmpeg is generating HLS files
* Ensure `/streams` directory is served

---

## 🎯 Conclusion

This project demonstrates:

* Real-time RTSP streaming
* RTSP to HLS conversion using FFmpeg
* Live overlay management with CRUD APIs
* React + Flask integration
* MongoDB persistence
* Real-world RTSP testing using a phone camera

