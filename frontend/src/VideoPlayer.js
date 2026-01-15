import React, {useRef, useEffect, useState} from 'react';
import Hls from 'hls.js';

export default function VideoPlayer({m3u8Path, overlays}){
  const videoRef = useRef(null);
  const hlsRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(1);
  const [loadingStatus, setLoadingStatus] = useState('');

  useEffect(()=>{
    const video = videoRef.current;
    if(!video) return;

    // Clean up previous HLS instance
    if(hlsRef.current){
      hlsRef.current.destroy();
      hlsRef.current = null;
    }

    if(m3u8Path){
      setLoadingStatus('⏳ Waiting for stream to initialize...');
      
      // Wait 5 seconds before trying to load (give FFmpeg time to create files)
      const initTimeout = setTimeout(() => {
        if(Hls.isSupported()){
          const hls = new Hls({
            enableWorker: true,
            lowLatencyMode: true,
            backBufferLength: 90,
            manifestLoadingTimeOut: 20000,
            manifestLoadingMaxRetry: 10,
            manifestLoadingRetryDelay: 2000,
            levelLoadingTimeOut: 20000,
            levelLoadingMaxRetry: 10,
            fragLoadingTimeOut: 30000
          });
          hlsRef.current = hls;
          
          setLoadingStatus('📡 Connecting to stream...');
          hls.loadSource(m3u8Path);
          hls.attachMedia(video);
          
          hls.on(Hls.Events.MANIFEST_PARSED, ()=>{
            setLoadingStatus('▶️ Starting playback...');
            video.play().then(()=>{
              setIsPlaying(true);
              setLoadingStatus('');
            }).catch(err=>{
              console.error('Autoplay failed:', err);
              setLoadingStatus('Click play button to start');
            });
          });

          hls.on(Hls.Events.ERROR, (event, data)=>{
            console.error('HLS Error:', data);
            if(data.fatal){
              switch(data.type){
                case Hls.ErrorTypes.NETWORK_ERROR:
                  if(data.details === 'manifestLoadError'){
                    setLoadingStatus('⏳ Stream not ready yet, retrying...');
                  } else {
                    setLoadingStatus('🔄 Network error, retrying...');
                  }
                  console.log('Network error, retrying...');
                  setTimeout(() => hls.startLoad(), 2000);
                  break;
                case Hls.ErrorTypes.MEDIA_ERROR:
                  console.log('Media error, recovering...');
                  setLoadingStatus('🔧 Recovering from media error...');
                  hls.recoverMediaError();
                  break;
                default:
                  setLoadingStatus('❌ Fatal error occurred');
                  hls.destroy();
                  break;
              }
            }
          });
        } else if(video.canPlayType('application/vnd.apple.mpegurl')){
          video.src = m3u8Path;
          video.play().then(()=>{
            setIsPlaying(true);
            setLoadingStatus('');
          });
        }
      }, 5000); // Wait 5 seconds before attempting to load

      return () => {
        clearTimeout(initTimeout);
        if(hlsRef.current){
          hlsRef.current.destroy();
        }
      };
    }
  }, [m3u8Path]);

  const togglePlay = ()=>{
    const video = videoRef.current;
    if(!video) return;
    if(video.paused){
      video.play();
      setIsPlaying(true);
    } else {
      video.pause();
      setIsPlaying(false);
    }
  };

  const handleVolumeChange = (e)=>{
    const val = parseFloat(e.target.value);
    setVolume(val);
    if(videoRef.current){
      videoRef.current.volume = val;
    }
  };

  return (
    <div className="video-container card">
      {!m3u8Path ? (
        <div className="video-placeholder">
          <div className="placeholder-content">
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            <p>Enter an RTSP URL and click Start Stream to begin</p>
          </div>
        </div>
      ) : (
        <>
          <div className="video-wrapper">
            {loadingStatus && (
              <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                backgroundColor: 'rgba(0,0,0,0.8)',
                color: 'white',
                padding: '20px 30px',
                borderRadius: '10px',
                fontSize: '18px',
                fontWeight: 'bold',
                zIndex: 10,
                textAlign: 'center',
                minWidth: '300px'
              }}>
                {loadingStatus}
              </div>
            )}
            <video ref={videoRef} className="video" />
            {overlays && overlays.map(o=> (
              <div 
                key={o._id} 
                className="overlay-display" 
                style={{
                  left: o.x,
                  top: o.y,
                  width: o.width,
                  height: o.height,
                  fontSize: o.type === 'text' ? `${Math.min(o.height * 0.6, 32)}px` : 'inherit'
                }}
              >
                {o.type === 'text' ? (
                  <span className="overlay-text">{o.content}</span>
                ) : (
                  <img src={o.content} alt="overlay" className="overlay-image" />
                )}
              </div>
            ))}
          </div>
          <div className="video-controls">
            <button className="control-btn" onClick={togglePlay}>
              {isPlaying ? '⏸' : '▶'}
            </button>
            <div className="volume-control">
              <span>🔊</span>
              <input 
                type="range" 
                min="0" 
                max="1" 
                step="0.1" 
                value={volume}
                onChange={handleVolumeChange}
                className="volume-slider"
              />
              <span className="volume-value">{Math.round(volume * 100)}%</span>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
