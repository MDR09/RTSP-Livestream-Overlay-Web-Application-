import React, {useState, useEffect} from 'react';
import VideoPlayer from './VideoPlayer';
import OverlayManager from './OverlayManager';
import axios from 'axios';

const API = process.env.REACT_APP_API || 'http://localhost:5000';

export default function App(){
  const [rtspUrl, setRtspUrl] = useState('rtsp://rtsp.stream/pattern');
  const [streamInfo, setStreamInfo] = useState(null);
  const [overlays, setOverlays] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [backendStatus, setBackendStatus] = useState('checking');

  useEffect(()=>{
    checkBackendHealth();
  }, []);

  useEffect(()=>{
    if(streamInfo){
      fetchOverlays();
      const interval = setInterval(fetchOverlays, 2000);
      return () => clearInterval(interval);
    }
  }, [streamInfo]);

  async function checkBackendHealth(){
    try{
      await axios.get(`${API}/api/overlays`, {timeout: 3000});
      setBackendStatus('connected');
      setError('');
    } catch(err){
      setBackendStatus('disconnected');
      setError('Backend not reachable. Ensure Flask is running on port 5000.');
    }
  }

  async function startStream(){
    if(!rtspUrl.trim()){
      setError('Please enter a valid RTSP URL');
      return;
    }
    setLoading(true);
    setError('');
    try{
      console.log('Starting stream with URL:', rtspUrl);
      const res = await axios.post(`${API}/api/stream/start`, {rtsp_url: rtspUrl}, {timeout: 15000});
      console.log('Stream response:', res.data);
      setStreamInfo(res.data);
      setBackendStatus('connected');
      setError('Stream started! Wait 10-15 seconds for video...');
      setTimeout(() => setError(''), 5000);
    } catch(err){
      console.error('Stream error:', err);
      if(err.code === 'ERR_NETWORK'){
        setError('Backend not reachable. Check if Flask is running on port 5000.');
      } else {
        setError(err.response?.data?.error || err.message || 'Failed to start stream');
      }
    } finally{
      setLoading(false);
    }
  }

  async function startTestStream(){
    setLoading(true);
    setError('');
    try{
      console.log('Starting TEST stream with generated pattern');
      const res = await axios.post(`${API}/api/stream/test`, {}, {timeout: 10000});
      console.log('Test stream response:', res.data);
      setStreamInfo(res.data);
      setBackendStatus('connected');
      setError('Test stream started! No network required.');
      setTimeout(() => setError(''), 5000);
    } catch(err){
      console.error('Test stream error:', err);
      setError(err.response?.data?.error || err.message || 'Failed to start test stream');
    } finally{
      setLoading(false);
    }
  }

  async function stopStream(){
    if(!streamInfo) return;
    try{
      await axios.post(`${API}/api/stream/${streamInfo.stream_id}/stop`);
      setStreamInfo(null);
      setOverlays([]);
    } catch(err){
      console.error('Stop error:', err);
    }
  }

  async function fetchOverlays(){
    if(!streamInfo) return;
    try{
      const res = await axios.get(`${API}/api/overlays?stream_id=${streamInfo.stream_id}`);
      setOverlays(res.data);
    } catch(err){
      console.error('Fetch overlays error:', err);
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>🎥 RTSP Livestream Overlay Application</h1>
        <div className="status-badge" data-status={backendStatus}>
          <span className="status-dot"></span>
          Backend: {backendStatus === 'connected' ? 'Connected' : 'Disconnected'}
          {backendStatus === 'disconnected' && (
            <button className="retry-btn" onClick={checkBackendHealth}>Retry</button>
          )}
        </div>
      </header>

      {error && (
        <div className="alert alert-error">
          <strong>⚠ Error:</strong> {error}
          <button className="close-btn" onClick={()=>setError('')}>×</button>
        </div>
      )}

      <div className="container">
        <div className="stream-section card">
          <h3>📡 Stream Configuration</h3>
          <div className="stream-controls">
            <input 
              type="text"
              className="rtsp-input"
              placeholder="Enter RTSP URL (e.g., rtsp://rtsp.stream/pattern)"
              value={rtspUrl}
              onChange={e=>setRtspUrl(e.target.value)}
              disabled={loading || streamInfo}
            />
            <button 
              className={streamInfo ? 'btn btn-danger' : 'btn btn-primary'}
              onClick={streamInfo ? stopStream : startStream}
              disabled={loading || backendStatus !== 'connected'}
            >
              {loading ? '⏳ Starting...' : streamInfo ? '⏹ Stop Stream' : '▶ Start Stream'}
            </button>
            <button 
              className="btn btn-secondary"
              onClick={startTestStream}
              disabled={loading || streamInfo || backendStatus !== 'connected'}
              style={{marginLeft: '10px'}}
            >
              🎨 Test Stream (No RTSP)
            </button>
          </div>
          {streamInfo && (
            <div className="stream-info">
              <span className="live-badge">🔴 LIVE</span>
              <span className="stream-id">Stream ID: {streamInfo.stream_id.substring(0, 8)}...</span>
            </div>
          )}
        </div>

        <div className="player-wrap">
          <VideoPlayer 
            m3u8Path={streamInfo?.hls_url || null} 
            overlays={overlays} 
          />
        </div>

        {streamInfo && (
          <OverlayManager 
            apiBase={API} 
            streamId={streamInfo.stream_id} 
            overlays={overlays} 
            refresh={fetchOverlays} 
          />
        )}
      </div>

      <footer className="footer">
        <p>RTSP Livestream Overlay App © 2026 | Built with React + Flask + MongoDB</p>
      </footer>
    </div>
  )
}
