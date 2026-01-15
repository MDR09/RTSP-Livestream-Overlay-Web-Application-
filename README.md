# RTSP Livestream Overlay Web Application

A professional web application that plays RTSP livestreams (converted to HLS) and allows real-time overlay management with drag-and-drop positioning and resizing.

## 🎯 Features

- ✅ **RTSP Stream Playback** - Automatic RTSP to HLS conversion using FFmpeg
- ✅ **Real-time Overlays** - Add text and image overlays on live video
- ✅ **Drag & Resize** - Move and resize overlays with mouse
- ✅ **CRUD Operations** - Complete API for overlay management
- ✅ **MongoDB Persistence** - All overlays saved to database
- ✅ **Modern UI** - Professional React interface with animations
- ✅ **Health Monitoring** - Backend status checks and error handling

## 📁 Project Structure

```
Assignment/
├── backend/              # Flask API Server
│   ├── app.py           # Main application
│   ├── requirements.txt # Python dependencies
│   ├── .env.example     # Environment variables template
│   └── streams/         # HLS output directory (auto-created)
├── frontend/            # React Web Application
│   ├── src/
│   │   ├── App.js          # Main component
│   │   ├── VideoPlayer.js  # HLS video player
│   │   ├── OverlayManager.js # Overlay CRUD UI
│   │   └── styles.css      # Professional styling
│   ├── package.json
│   └── public/
└── README.md
```

## 🔧 Prerequisites

Before starting, ensure you have:

1. **Python 3.8+** - [Download](https://www.python.org/downloads/)
2. **Node.js 16+** - [Download](https://nodejs.org/)
3. **MongoDB** - [Download](https://www.mongodb.com/try/download/community)
4. **FFmpeg** - [Download](https://ffmpeg.org/download.html) ⚠️ **IMPORTANT**

### Installing FFmpeg (Windows)

1. Download FFmpeg from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to System PATH:
   - Search "Environment Variables" in Windows
   - Edit "Path" under System Variables
   - Add new entry: `C:\ffmpeg\bin`
   - Restart terminal

Verify installation:
```bash
ffmpeg -version
```

## 🚀 Setup Instructions

### Backend Setup

1. **Navigate to backend directory:**
```bash
cd backend
```

2. **Create Python virtual environment:**
```bash
python -m venv venv
```

3. **Activate virtual environment:**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Configure environment (optional):**
```bash
# Copy example env file
copy .env.example .env

# Edit .env if needed (defaults work for local development)
```

6. **Start MongoDB:**
```bash
# Windows (if installed as service)
net start MongoDB

# Or run mongod manually
mongod
```

7. **Run the backend server:**
```bash
python app.py
```

Backend will start on **http://localhost:5000**

**✅ Expected Output:**
```
============================================================
RTSP Livestream Overlay Backend Server
============================================================
✓ MongoDB connected successfully
✓ FFmpeg is available
Starting Flask server on http://0.0.0.0:5000
Press CTRL+C to stop
```

### Frontend Setup

1. **Open new terminal and navigate to frontend:**
```bash
cd frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Start development server:**
```bash
npm start
```

Frontend will open automatically at **http://localhost:3000**

## 📖 Usage Guide

### 1. Start a Stream

1. Enter an RTSP URL in the input field:
   - Example: `rtsp://rtsp.stream/pattern`
   - Or: `rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4`

2. Click **"▶ Start Stream"**

3. Wait 5-10 seconds for FFmpeg to process the stream

4. Video will start playing automatically

### 2. Add Overlays

**Text Overlay:**
1. Select "📝 Text Overlay" from dropdown
2. Type your text or click a preset button
3. Click "➕ Add Overlay"

**Image Overlay:**
1. Select "🖼 Image Overlay" from dropdown
2. Enter image URL (must be publicly accessible)
3. Click "➕ Add Overlay"

### 3. Manage Overlays

- **Move:** Click and drag the overlay preview
- **Resize:** Drag the corners of the overlay
- **Edit:** Click ✏️ to change content
- **Delete:** Click 🗑 to remove overlay

All changes are saved to MongoDB automatically!

## 🔌 API Documentation

### Base URL
```
http://localhost:5000/api
```

### Endpoints

#### Health Check
```http
GET /api/health
```
**Response:**
```json
{
  "status": "healthy",
  "mongodb": "connected",
  "ffmpeg": "available",
  "active_streams": 1
}
```

#### Start Stream
```http
POST /api/stream
Content-Type: application/json

{
  "rtsp_url": "rtsp://rtsp.stream/pattern"
}
```
**Response:**
```json
{
  "stream_id": "abc-123-def-456",
  "m3u8_path": "/streams/abc-123-def-456/index.m3u8",
  "status": "starting"
}
```

#### Stop Stream
```http
POST /api/stream/{stream_id}/stop
```

#### List Streams
```http
GET /api/streams
```

#### Create Overlay
```http
POST /api/overlays
Content-Type: application/json

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

#### Get All Overlays
```http
GET /api/overlays?stream_id=default
```

#### Get Single Overlay
```http
GET /api/overlays/{overlay_id}
```

#### Update Overlay
```http
PUT /api/overlays/{overlay_id}
Content-Type: application/json

{
  "x": 100,
  "y": 200,
  "content": "Updated Text"
}
```

#### Delete Overlay
```http
DELETE /api/overlays/{overlay_id}
```

#### Bulk Delete Overlays
```http
POST /api/overlays/bulk-delete
Content-Type: application/json

{
  "overlay_ids": ["id1", "id2", "id3"]
}
```

## 🧪 Testing

### Test with cURL

**Health Check:**
```bash
curl http://localhost:5000/api/health
```

**Start Stream:**
```bash
curl -X POST http://localhost:5000/api/stream -H "Content-Type: application/json" -d "{\"rtsp_url\":\"rtsp://rtsp.stream/pattern\"}"
```

**Create Overlay:**
```bash
curl -X POST http://localhost:5000/api/overlays -H "Content-Type: application/json" -d "{\"type\":\"text\",\"content\":\"LIVE\",\"stream_id\":\"default\"}"
```

### Test RTSP URLs

Free RTSP test streams:
- `rtsp://rtsp.stream/pattern` - Test pattern
- `rtsp://rtsp.stream/movie` - Sample movie
- `rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4` - Big Buck Bunny

## 🎬 Demo Video Requirements

Record a screen capture showing:

1. ✅ Starting backend (showing successful MongoDB + FFmpeg checks)
2. ✅ Starting frontend
3. ✅ Entering RTSP URL and starting stream
4. ✅ Creating text overlay with preset
5. ✅ Creating image overlay with URL
6. ✅ Dragging overlays to different positions
7. ✅ Resizing overlays
8. ✅ Editing overlay content
9. ✅ Deleting an overlay
10. ✅ Showing real-time updates on video

## 🛠 Troubleshooting

### Backend Issues

**MongoDB Connection Failed:**
```bash
# Check if MongoDB is running
mongod --version

# Start MongoDB service (Windows)
net start MongoDB
```

**FFmpeg Not Found:**
```bash
# Verify FFmpeg is in PATH
ffmpeg -version

# If not found, reinstall and add to PATH
```

**Port 5000 Already in Use:**
```bash
# Find and kill process using port 5000 (Windows)
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Frontend Issues

**Network Error:**
- Ensure backend is running on port 5000
- Check browser console for errors
- Verify CORS is enabled
