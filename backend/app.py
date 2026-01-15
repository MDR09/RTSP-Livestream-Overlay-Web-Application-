from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import os
import subprocess
import uuid
from datetime import datetime
import logging
import signal
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# CORS Configuration - Allow both port 3000 and 3001
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"], 
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# MongoDB connection with Atlas support
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
logger.info(f"Connecting to MongoDB...")

try:
    # MongoDB Atlas requires retryWrites and w=majority for reliability
    client = MongoClient(
        MONGO_URI, 
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000,
        retryWrites=True
    )
    
    # Test connection
    client.admin.command('ping')
    db = client['rtsp_overlay_db']
    overlays_collection = db['overlays']
    
    # Create indexes for better performance
    overlays_collection.create_index('created_at')
    
    logger.info("✅ MongoDB connected successfully (Atlas Cloud)")
    USE_MONGODB = True
except Exception as e:
    logger.error(f"❌ MongoDB connection failed: {e}")
    logger.warning("⚠️  Using in-memory storage as fallback")
    db = None
    overlays_collection = None
    USE_MONGODB = False

# In-memory fallback storage
in_memory_overlays = []

# Store active streams
active_streams = {}

# Create streams directory
STREAMS_DIR = os.path.join(os.path.dirname(__file__), 'streams')
os.makedirs(STREAMS_DIR, exist_ok=True)

# Check ffmpeg availability
def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      check=True)
        logger.info("✅ FFmpeg is available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("❌ FFmpeg not found. Please install FFmpeg and add to PATH")
        return False

ffmpeg_available = check_ffmpeg()

# ==================== HEALTH CHECK ====================
@app.route('/api/health', methods=['GET'])
def health_check():
    """Check backend health and dependencies"""
    try:
        mongodb_status = "connected"
        if overlays_collection is not None:
            client.admin.command('ping')
        else:
            mongodb_status = "disconnected"
        
        return jsonify({
            "status": "healthy",
            "mongodb": mongodb_status,
            "ffmpeg": "available" if ffmpeg_available else "not found",
            "active_streams": len(active_streams)
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

# ==================== STREAM MANAGEMENT ====================
@app.route('/api/stream/test', methods=['POST'])
def start_test_stream():
    """Start a test stream using testsrc (FFmpeg built-in test pattern)"""
    if not ffmpeg_available:
        return jsonify({"error": "FFmpeg not available"}), 500
    
    stream_id = str(uuid.uuid4())
    stream_dir = os.path.join(STREAMS_DIR, stream_id)
    os.makedirs(stream_dir, exist_ok=True)
    
    hls_path = os.path.join(stream_dir, 'index.m3u8')
    
    # Use FFmpeg's testsrc to generate a test pattern (no network required)
    ffmpeg_cmd = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', 'testsrc=duration=300:size=1280x720:rate=30',
        '-f', 'lavfi',
        '-i', 'sine=frequency=1000:duration=300',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-c:a', 'aac',
        '-f', 'hls',
        '-hls_time', '2',
        '-hls_list_size', '10',
        '-hls_flags', 'delete_segments+append_list',
        '-hls_segment_filename', os.path.join(stream_dir, 'segment_%03d.ts'),
        '-y',  # Overwrite output files
        hls_path
    ]
    
    try:
        logger.info(f"Starting TEST stream with generated pattern")
        
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout
            universal_newlines=True
        )
        
        active_streams[stream_id] = {
            'process': process,
            'rtsp_url': 'test://pattern',
            'hls_path': hls_path,
            'started_at': datetime.utcnow().isoformat()
        }
        
        # Start a background thread to log FFmpeg output
        def log_ffmpeg_output():
            for line in process.stdout:
                logger.info(f"[FFmpeg-TEST {stream_id[:8]}] {line.strip()}")
        
        import threading
        log_thread = threading.Thread(target=log_ffmpeg_output, daemon=True)
        log_thread.start()
        
        logger.info(f"🎥 Test stream started: {stream_id}")
        
        return jsonify({
            'stream_id': stream_id,
            'hls_url': f'http://localhost:5000/streams/{stream_id}/index.m3u8',
            'status': 'started',
            'message': 'Test stream started with generated pattern'
        }), 200
        
    except Exception as e:
        logger.error(f"Error starting test stream: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/stream/start', methods=['POST'])
def start_stream():
    """Start RTSP to HLS conversion"""
    if not ffmpeg_available:
        return jsonify({"error": "FFmpeg not available"}), 500
    
    data = request.get_json()
    rtsp_url = data.get('rtsp_url')
    
    if not rtsp_url:
        return jsonify({"error": "rtsp_url is required"}), 400
    
    if not rtsp_url.startswith('rtsp://'):
        return jsonify({"error": "Invalid RTSP URL format"}), 400
    
    # Generate unique stream ID
    stream_id = str(uuid.uuid4())
    stream_dir = os.path.join(STREAMS_DIR, stream_id)
    os.makedirs(stream_dir, exist_ok=True)
    
    # HLS output path
    hls_path = os.path.join(stream_dir, 'index.m3u8')
    
    # FFmpeg command to convert RTSP to HLS
    ffmpeg_cmd = [
        'ffmpeg',
        '-rtsp_transport', 'tcp',
        '-timeout', '10000000',  # 10 second timeout for RTSP connection
        '-i', rtsp_url,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-f', 'hls',
        '-hls_time', '2',
        '-hls_list_size', '10',
        '-hls_flags', 'delete_segments+append_list',
        '-hls_segment_filename', os.path.join(stream_dir, 'segment_%03d.ts'),
        '-y',  # Overwrite output files
        hls_path
    ]
    
    try:
        # Start FFmpeg process with better error capture
        logger.info(f"Starting FFmpeg with command: {' '.join(ffmpeg_cmd)}")
        
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout
            universal_newlines=True
        )
        
        # Store stream info
        active_streams[stream_id] = {
            'process': process,
            'rtsp_url': rtsp_url,
            'hls_path': hls_path,
            'started_at': datetime.utcnow().isoformat()
        }
        
        # Start a background thread to log FFmpeg output
        def log_ffmpeg_output():
            for line in process.stdout:
                logger.info(f"[FFmpeg {stream_id[:8]}] {line.strip()}")
        
        import threading
        log_thread = threading.Thread(target=log_ffmpeg_output, daemon=True)
        log_thread.start()
        
        logger.info(f"🎥 Stream started: {stream_id} from {rtsp_url}")
        logger.info(f"📁 HLS output: {hls_path}")
        logger.info(f"⏳ Please wait 10-15 seconds for HLS segments to be created...")
        
        # Check if process started successfully
        import time
        time.sleep(1)
        if process.poll() is not None:
            # Process already terminated - there was an error
            _, stderr = process.communicate()
            logger.error(f"FFmpeg failed immediately: {stderr}")
            return jsonify({
                "error": f"FFmpeg failed to start. Check RTSP URL or FFmpeg installation.",
                "details": stderr[:500]
            }), 500
        
        return jsonify({
            'stream_id': stream_id,
            'hls_url': f'http://localhost:5000/streams/{stream_id}/index.m3u8',
            'status': 'started',
            'message': 'Stream started. Please wait 10-15 seconds for video to load.'
        }), 200
        
    except Exception as e:
        logger.error(f"Error starting stream: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stream/stop', methods=['POST'])
@app.route('/api/stream/<stream_id>/stop', methods=['POST'])
def stop_stream(stream_id=None):
    """Stop an active stream"""
    if not stream_id:
        data = request.get_json()
        stream_id = data.get('stream_id')
    
    if not stream_id or stream_id not in active_streams:
        return jsonify({"error": "Stream not found"}), 404
    
    try:
        # Terminate FFmpeg process
        process = active_streams[stream_id]['process']
        process.terminate()
        process.wait(timeout=5)
        
        # Clean up
        del active_streams[stream_id]
        logger.info(f"🛑 Stream stopped: {stream_id}")
        
        return jsonify({"status": "stopped"}), 200
        
    except Exception as e:
        logger.error(f"Error stopping stream: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stream/status', methods=['GET'])
def stream_status():
    """Get status of all active streams"""
    streams = []
    for stream_id, info in active_streams.items():
        streams.append({
            'stream_id': stream_id,
            'rtsp_url': info['rtsp_url'],
            'started_at': info['started_at'],
            'running': info['process'].poll() is None
        })
    
    return jsonify({'active_streams': streams}), 200

# ==================== SERVE HLS STREAMS ====================
@app.route('/streams/<stream_id>/<filename>', methods=['GET'])
def serve_stream(stream_id, filename):
    """Serve HLS playlist and segments"""
    stream_dir = os.path.join(STREAMS_DIR, stream_id)
    
    if not os.path.exists(stream_dir):
        logger.error(f"Stream directory not found: {stream_dir}")
        return jsonify({"error": "Stream not found"}), 404
    
    file_path = os.path.join(stream_dir, filename)
    if not os.path.exists(file_path):
        logger.warning(f"File not found yet: {file_path}")
        return jsonify({"error": f"File {filename} not ready yet. Please wait..."}), 404
    
    # Set proper content type
    if filename.endswith('.m3u8'):
        return send_from_directory(stream_dir, filename, mimetype='application/vnd.apple.mpegurl')
    elif filename.endswith('.ts'):
        return send_from_directory(stream_dir, filename, mimetype='video/mp2t')
    else:
        return send_from_directory(stream_dir, filename)

# ==================== OVERLAY CRUD ====================
@app.route('/api/overlays', methods=['GET'])
def get_overlays():
    """Get all overlays"""
    if USE_MONGODB:
        if overlays_collection is None:
            return jsonify({"error": "Database not available"}), 503
        
        try:
            overlays = list(overlays_collection.find().sort('created_at', -1))
            for overlay in overlays:
                overlay['_id'] = str(overlay['_id'])
                # Convert datetime to string if needed
                if 'created_at' in overlay and hasattr(overlay['created_at'], 'isoformat'):
                    overlay['created_at'] = overlay['created_at'].isoformat()
                if 'updated_at' in overlay and hasattr(overlay['updated_at'], 'isoformat'):
                    overlay['updated_at'] = overlay['updated_at'].isoformat()
            
            logger.info(f"📋 Retrieved {len(overlays)} overlays")
            return jsonify(overlays), 200
            
        except Exception as e:
            logger.error(f"Error fetching overlays: {e}")
            return jsonify({"error": str(e)}), 500
    else:
        # Return in-memory overlays
        return jsonify(in_memory_overlays), 200

@app.route('/api/overlays', methods=['POST'])
def create_overlay():
    """Create a new overlay"""
    data = request.get_json()
    
    # Validate required fields
    if not data.get('type') or data['type'] not in ['text', 'image']:
        return jsonify({"error": "Invalid overlay type. Must be 'text' or 'image'"}), 400
    
    if not data.get('content'):
        return jsonify({"error": "Content is required"}), 400
    
    # Set defaults
    overlay = {
        'type': data['type'],
        'content': data['content'],
        'position': data.get('position', {'x': 50, 'y': 50}),
        'size': data.get('size', {'width': 200, 'height': 100}),
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    # Validate dimensions
    if overlay['size']['width'] < 10 or overlay['size']['width'] > 2000:
        return jsonify({"error": "Width must be between 10 and 2000"}), 400
    if overlay['size']['height'] < 10 or overlay['size']['height'] > 2000:
        return jsonify({"error": "Height must be between 10 and 2000"}), 400
    
    if USE_MONGODB:
        try:
            # Convert to datetime for MongoDB
            mongo_overlay = overlay.copy()
            mongo_overlay['created_at'] = datetime.utcnow()
            mongo_overlay['updated_at'] = datetime.utcnow()
            
            result = overlays_collection.insert_one(mongo_overlay)
            overlay['_id'] = str(result.inserted_id)
            
            logger.info(f"✅ Overlay created: {overlay['_id']} ({overlay['type']})")
            return jsonify(overlay), 201
            
        except Exception as e:
            logger.error(f"Error creating overlay: {e}")
            return jsonify({"error": str(e)}), 500
    else:
        # Use in-memory storage
        overlay['_id'] = str(uuid.uuid4())
        in_memory_overlays.append(overlay)
        logger.info(f"✅ Overlay created (in-memory): {overlay['_id']} ({overlay['type']})")
        return jsonify(overlay), 201

@app.route('/api/overlays/<overlay_id>', methods=['GET'])
def get_overlay(overlay_id):
    """Get a specific overlay"""
    if overlays_collection is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        overlay = overlays_collection.find_one({'_id': ObjectId(overlay_id)})
        
        if not overlay:
            return jsonify({"error": "Overlay not found"}), 404
        
        overlay['_id'] = str(overlay['_id'])
        return jsonify(overlay), 200
        
    except Exception as e:
        logger.error(f"Error fetching overlay: {e}")
        return jsonify({"error": "Invalid overlay ID"}), 400

@app.route('/api/overlays/<overlay_id>', methods=['PUT'])
def update_overlay(overlay_id):
    """Update an existing overlay"""
    data = request.get_json()
    
    # Validate overlay type if provided
    if 'type' in data and data['type'] not in ['text', 'image']:
        return jsonify({"error": "Invalid overlay type"}), 400
    
    # Validate dimensions if provided
    if 'size' in data:
        if data['size']['width'] < 10 or data['size']['width'] > 2000:
            return jsonify({"error": "Width must be between 10 and 2000"}), 400
        if data['size']['height'] < 10 or data['size']['height'] > 2000:
            return jsonify({"error": "Height must be between 10 and 2000"}), 400
    
    if USE_MONGODB:
        try:
            # Add updated timestamp
            data['updated_at'] = datetime.utcnow()
            
            result = overlays_collection.update_one(
                {'_id': ObjectId(overlay_id)},
                {'$set': data}
            )
            
            if result.matched_count == 0:
                return jsonify({"error": "Overlay not found"}), 404
            
            # Get updated overlay
            overlay = overlays_collection.find_one({'_id': ObjectId(overlay_id)})
            overlay['_id'] = str(overlay['_id'])
            if 'created_at' in overlay and hasattr(overlay['created_at'], 'isoformat'):
                overlay['created_at'] = overlay['created_at'].isoformat()
            if 'updated_at' in overlay and hasattr(overlay['updated_at'], 'isoformat'):
                overlay['updated_at'] = overlay['updated_at'].isoformat()
            
            logger.info(f"✏️ Overlay updated: {overlay_id}")
            return jsonify(overlay), 200
            
        except Exception as e:
            logger.error(f"Error updating overlay: {e}")
            return jsonify({"error": "Invalid overlay ID"}), 400
    else:
        # Use in-memory storage
        for overlay in in_memory_overlays:
            if overlay['_id'] == overlay_id:
                overlay.update(data)
                overlay['updated_at'] = datetime.utcnow().isoformat()
                logger.info(f"✏️ Overlay updated (in-memory): {overlay_id}")
                return jsonify(overlay), 200
        
        return jsonify({"error": "Overlay not found"}), 404

@app.route('/api/overlays/<overlay_id>', methods=['DELETE'])
def delete_overlay(overlay_id):
    """Delete an overlay"""
    if USE_MONGODB:
        try:
            result = overlays_collection.delete_one({'_id': ObjectId(overlay_id)})
            
            if result.deleted_count == 0:
                return jsonify({"error": "Overlay not found"}), 404
            
            logger.info(f"🗑️ Overlay deleted: {overlay_id}")
            return jsonify({"message": "Overlay deleted successfully"}), 200
            
        except Exception as e:
            logger.error(f"Error deleting overlay: {e}")
            return jsonify({"error": "Invalid overlay ID"}), 400
    else:
        # Use in-memory storage
        global in_memory_overlays
        original_length = len(in_memory_overlays)
        in_memory_overlays = [o for o in in_memory_overlays if o['_id'] != overlay_id]
        
        if len(in_memory_overlays) == original_length:
            return jsonify({"error": "Overlay not found"}), 404
        
        logger.info(f"🗑️ Overlay deleted (in-memory): {overlay_id}")
        return jsonify({"message": "Overlay deleted successfully"}), 200

@app.route('/api/overlays/bulk-delete', methods=['POST'])
def bulk_delete_overlays():
    """Delete multiple overlays"""
    if overlays_collection is None:
        return jsonify({"error": "Database not available"}), 503
    
    data = request.get_json()
    overlay_ids = data.get('overlay_ids', [])
    
    if not overlay_ids:
        return jsonify({"error": "No overlay IDs provided"}), 400
    
    try:
        object_ids = [ObjectId(id) for id in overlay_ids]
        result = overlays_collection.delete_many({'_id': {'$in': object_ids}})
        
        logger.info(f"🗑️ Bulk deleted {result.deleted_count} overlays")
        return jsonify({
            "message": f"Deleted {result.deleted_count} overlays",
            "deleted_count": result.deleted_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error bulk deleting overlays: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== CLEANUP ====================
def cleanup_streams():
    """Clean up all active streams on shutdown"""
    logger.info("🧹 Cleaning up active streams...")
    for stream_id, info in list(active_streams.items()):
        try:
            process = info['process']
            process.terminate()
            process.wait(timeout=5)
            logger.info(f"Stopped stream: {stream_id}")
        except Exception as e:
            logger.error(f"Error stopping stream {stream_id}: {e}")

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("🛑 Shutting down gracefully...")
    cleanup_streams()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ==================== RUN SERVER ====================
if __name__ == '__main__':
    logger.info("🚀 Starting RTSP Overlay Server...")
    logger.info(f"📁 Streams directory: {STREAMS_DIR}")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        cleanup_streams()

