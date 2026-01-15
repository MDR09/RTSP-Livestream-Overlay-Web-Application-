import React, {useState} from 'react';
import axios from 'axios';
import { Rnd } from 'react-rnd';

export default function OverlayManager({apiBase, streamId, overlays, refresh}){
  const [type, setType] = useState('text');
  const [content, setContent] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editContent, setEditContent] = useState('');

  async function create(){
    if(!content.trim()){
      alert('Please enter content for the overlay');
      return;
    }
    try{
      await axios.post(`${apiBase}/api/overlays`, {
        type, 
        content: content.trim(), 
        stream_id: streamId,
        x: 50,
        y: 50,
        width: type === 'text' ? 200 : 150,
        height: type === 'text' ? 60 : 100
      });
      setContent('');
      refresh();
    } catch(err){
      console.error('Create error:', err);
      alert('Failed to create overlay');
    }
  }

  async function remove(id){
    if(!window.confirm('Delete this overlay?')) return;
    try{
      await axios.delete(`${apiBase}/api/overlays/${id}`);
      refresh();
    } catch(err){
      console.error('Delete error:', err);
    }
  }

  async function updatePos(id, data){
    try{
      await axios.put(`${apiBase}/api/overlays/${id}`, data);
      refresh();
    } catch(err){
      console.error('Update error:', err);
    }
  }

  async function saveEdit(id){
    if(!editContent.trim()) return;
    try{
      await axios.put(`${apiBase}/api/overlays/${id}`, {content: editContent.trim()});
      setEditingId(null);
      setEditContent('');
      refresh();
    } catch(err){
      console.error('Edit error:', err);
    }
  }

  function startEdit(overlay){
    setEditingId(overlay._id);
    setEditContent(overlay.content);
  }

  const presetTexts = ['LIVE', 'Breaking News', 'Subscribe Now', 'NEW'];
  const presetImages = [
    'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Google_2015_logo.svg/200px-Google_2015_logo.svg.png',
    'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Logo_TV_2015.svg/200px-Logo_TV_2015.svg.png'
  ];

  return (
    <div className="overlay-manager card">
      <h3>🎨 Overlay Management</h3>
      
      <div className="overlay-creator">
        <div className="form-group">
          <label>Overlay Type:</label>
          <select value={type} onChange={e=>setType(e.target.value)} className="select-input">
            <option value="text">📝 Text Overlay</option>
            <option value="image">🖼 Image Overlay</option>
          </select>
        </div>

        <div className="form-group">
          <label>{type === 'text' ? 'Text Content:' : 'Image URL:'}}</label>
          <input 
            value={content} 
            onChange={e=>setContent(e.target.value)}
            placeholder={type === 'text' ? 'Enter text...' : 'Enter image URL...'}
            className="text-input"
            onKeyPress={e=>e.key==='Enter' && create()}
          />
        </div>

        {type === 'text' && (
          <div className="preset-buttons">
            {presetTexts.map(txt=>(
              <button key={txt} className="preset-btn" onClick={()=>setContent(txt)}>{txt}</button>
            ))}
          </div>
        )}

        {type === 'image' && (
          <div className="preset-buttons">
            {presetImages.map((url, i)=>(
              <button key={i} className="preset-btn" onClick={()=>setContent(url)}>Sample {i+1}</button>
            ))}
          </div>
        )}

        <button className="btn btn-success btn-block" onClick={create}>
          ➕ Add Overlay
        </button>
      </div>

      <div className="overlays-list">
        <h4>Active Overlays ({overlays.length})</h4>
        {overlays.length === 0 ? (
          <div className="empty-state">
            <p>No overlays yet. Create one above!</p>
          </div>
        ) : (
          overlays.map(o=> (
            <div key={o._id} className="overlay-item">
              <div className="overlay-header">
                <div className="overlay-meta">
                  <span className="overlay-type-badge">{o.type === 'text' ? '📝' : '🖼'}</span>
                  {editingId === o._id ? (
                    <input 
                      value={editContent}
                      onChange={e=>setEditContent(e.target.value)}
                      className="edit-input"
                      autoFocus
                    />
                  ) : (
                    <span className="overlay-content-preview">
                      {o.type === 'text' ? o.content : o.content.substring(0, 40) + '...'}
                    </span>
                  )}
                </div>
                <div className="overlay-actions">
                  {editingId === o._id ? (
                    <>
                      <button className="btn-icon btn-success" onClick={()=>saveEdit(o._id)} title="Save">✓</button>
                      <button className="btn-icon" onClick={()=>{setEditingId(null);setEditContent('');}} title="Cancel">✕</button>
                    </>
                  ) : (
                    <>
                      <button className="btn-icon" onClick={()=>startEdit(o)} title="Edit">✏️</button>
                      <button className="btn-icon btn-danger" onClick={()=>remove(o._id)} title="Delete">🗑</button>
                    </>
                  )}
                </div>
              </div>
              <div className="overlay-preview">
                <small>Position: ({o.x}, {o.y}) | Size: {o.width}×{o.height}px</small>
                <div className="preview-box">
                  <Rnd
                    size={{ width: Math.min(o.width, 300), height: Math.min(o.height, 200) }}
                    position={{ x: 10, y: 10 }}
                    minWidth={50}
                    minHeight={30}
                    bounds="parent"
                    onDragStop={(e, d)=> updatePos(o._id, {x: Math.round(d.x), y: Math.round(d.y)})}
                    onResizeStop={(e, dir, ref, delta, pos)=> updatePos(o._id, {
                      width: parseInt(ref.style.width), 
                      height: parseInt(ref.style.height), 
                      x: Math.round(pos.x), 
                      y: Math.round(pos.y)
                    })}
                    className="rnd-overlay"
                  >
                    <div className="rnd-content">
                      {o.type === 'text' ? (
                        <span style={{fontSize: `${Math.min(o.height * 0.4, 24)}px`}}>{o.content}</span>
                      ) : (
                        <img src={o.content} alt="preview" className="rnd-image" />
                      )}
                    </div>
                  </Rnd>
                </div>
                <small className="hint">💡 Drag to move, drag corners to resize</small>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
