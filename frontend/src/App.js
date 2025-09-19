import React, { useEffect, useRef, useState } from 'react';

const API_BASE = 'http://localhost:8000';

export default function App() {
  const imgRef = useRef(null);
  const canvasRef = useRef(null);
  const idInputRef = useRef(null);

  const [frameUrl, setFrameUrl] = useState(`${API_BASE}/api/frame.jpg?ts=${Date.now()}`);
  const [detections, setDetections] = useState({ frame_size: [0, 0], detections: [] });
  const [soldiers, setSoldiers] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const beepRef = useRef(null);
  const [soundEnabled, setSoundEnabled] = useState(false);

  // Refresh image every 1s to avoid caching
  useEffect(() => {
    const id = setInterval(() => {
      setFrameUrl(`${API_BASE}/api/frame.jpg?ts=${Date.now()}`);
    }, 1000);
    return () => clearInterval(id);
  }, []);

  // Poll detections every 1s
  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/detections`);
        const json = await res.json();
        setDetections(json);
      } catch (e) {
        // swallow
      }
    }, 1000);
    return () => clearInterval(id);
  }, []);

  // Draw detections on canvas overlay scaled to displayed image
  useEffect(() => {
    const img = imgRef.current;
    const canvas = canvasRef.current;
    if (!img || !canvas) return;

    const ctx = canvas.getContext('2d');
    const dispW = img.clientWidth;
    const dispH = img.clientHeight;
    canvas.width = dispW;
    canvas.height = dispH;

    ctx.clearRect(0, 0, dispW, dispH);

    const [frameW, frameH] = detections.frame_size || [0, 0];
    if (!frameW || !frameH) return;
    const scaleX = dispW / frameW;
    const scaleY = dispH / frameH;

    let unknownPresent = false;
    const criminalIds = new Set();
    (detections.detections || []).forEach(d => {
      const [x, y, w, h] = d.bbox;
      const sx = x * scaleX;
      const sy = y * scaleY;
      const sw = w * scaleX;
      const sh = h * scaleY;

      const isMatch = !!d.face_match;
      // Color by category
      if (isMatch) {
        if (d.category === 'official') ctx.strokeStyle = 'lime';
        else if (d.category === 'citizen') ctx.strokeStyle = 'yellow';
        else if (d.category === 'criminal') ctx.strokeStyle = 'red';
        else ctx.strokeStyle = 'lime';
      } else {
        ctx.strokeStyle = 'orange';
      }
      ctx.lineWidth = 2;
      ctx.strokeRect(sx, sy, sw, sh);
      if (isMatch) {
        if (d.category === 'official') ctx.fillStyle = 'rgba(0,255,0,0.2)';
        else if (d.category === 'citizen') ctx.fillStyle = 'rgba(255,255,0,0.2)';
        else if (d.category === 'criminal') ctx.fillStyle = 'rgba(255,0,0,0.2)';
        else ctx.fillStyle = 'rgba(0,255,0,0.2)';
      } else {
        ctx.fillStyle = 'rgba(255,165,0,0.25)';
      }
      ctx.fillRect(sx, sy, sw, sh);
      ctx.fillStyle = 'white';
      ctx.font = '12px sans-serif';
      let label = 'unknown';
      if (isMatch) {
        if (d.category === 'official') label = `Official: ${d.label}`;
        else if (d.category === 'citizen') label = `Citizen: ${d.label}`;
        else if (d.category === 'criminal') label = `Criminal: ${d.label}`;
        else label = `Known: ${d.label}`;
      }
      ctx.fillText(label, sx + 4, sy - 4 < 10 ? sy + 12 : sy - 4);

      if (!isMatch) unknownPresent = true;
      if (isMatch && d.category === 'criminal' && d.label) criminalIds.add(d.label);
    });

    if (criminalIds.size > 0) {
      triggerAlert(`Criminal alert: ${Array.from(criminalIds).join(', ')}`);
    }
    if (unknownPresent) {
      triggerAlert('Unknown person detected');
    }
  }, [detections, frameUrl]);

  // Poll soldiers every 3s
  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/soldiers`);
        const json = await res.json();
        const list = json.soldiers || [];
        setSoldiers(list);
        if (list.some(s => s.status === 'critical')) {
          triggerAlert('Critical soldier status');
        }
      } catch (e) {}
    }, 3000);
    return () => clearInterval(id);
  }, []);

  const triggerAlert = (message) => {
    setAlerts(prev => [{ ts: Date.now(), message }, ...prev].slice(0, 50));
    if (soundEnabled) {
      try {
        if (beepRef.current) {
          beepRef.current.currentTime = 0;
          beepRef.current.play();
        }
      } catch (e) {}
    }
  };

  const enableSound = async () => {
    try {
      if (beepRef.current) {
        // Attempt a play/pause cycle to unlock autoplay
        await beepRef.current.play();
        beepRef.current.pause();
        beepRef.current.currentTime = 0;
        setSoundEnabled(true);
      }
    } catch (e) {
      // If still blocked, user may need to click again
    }
  };

  const onSubmitRegister = async (e) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const id = form.get('id');
    const file = form.get('file');
    const category = form.get('category') || 'citizen';
    if (!id || !file) return;
    try {
      form.set('category', category);
      await fetch(`${API_BASE}/api/register-face`, { method: 'POST', body: form });
      triggerAlert(`Registered face for ${id}`);
      e.currentTarget.reset();
    } catch (e) {}
  };

  return (
    <div className="max-w-7xl mx-auto p-4 md:p-6 space-y-5">
      <audio ref={beepRef} src="data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAABCxAgAEABAAZGF0YQAAAAA=" preload="auto" />

      <div className="flex items-center justify-between">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight">VeerDrishti</h1>
        <div className="text-xs md:text-sm text-slate-500">Live Vision · Simple CPU Pipeline</div>
      </div>

      {!soundEnabled && (
        <div className="p-2 bg-yellow-100 text-yellow-900 rounded flex items-center justify-between">
          <span>Click to enable alert sounds (browser autoplay policy).</span>
          <button onClick={enableSound} className="ml-3 px-3 py-1 bg-yellow-600 text-white rounded">Enable Sound</button>
        </div>
      )}

      <div className="grid md:grid-cols-3 gap-5">
        <div className="md:col-span-2">
          <div className="relative w-full overflow-hidden rounded-xl shadow ring-1 ring-slate-200 bg-white">
            <img ref={imgRef} crossOrigin="anonymous" src={frameUrl} alt="live" className="w-full h-auto" />
            <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />
          </div>
        </div>
        <div className="space-y-3">
          <form onSubmit={onSubmitRegister} className="p-4 bg-white rounded-xl shadow ring-1 ring-slate-200 space-y-3">
            <h2 className="font-semibold">Register Face</h2>
            <input ref={idInputRef} name="id" className="w-full border p-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="ID" />
            <select name="category" defaultValue="citizen" className="w-full border p-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="citizen">Citizen (yellow)</option>
              <option value="official">Official (green)</option>
              <option value="criminal">Criminal (red)</option>
            </select>
            <input name="file" type="file" accept="image/*" className="w-full" />
            <button className="w-full bg-blue-600 hover:bg-blue-700 transition text-white py-2 rounded">Submit</button>
            <button type="button" onClick={async () => {
              const idVal = idInputRef.current?.value?.trim();
              const img = imgRef.current;
              if (!idVal) { alert('Enter ID first'); return; }
              if (!img || !img.complete) { alert('Live image not ready'); return; }
              try {
                const w = img.naturalWidth || img.width;
                const h = img.naturalHeight || img.height;
                const off = document.createElement('canvas');
                off.width = w; off.height = h;
                const ctx = off.getContext('2d');
                ctx.drawImage(img, 0, 0, w, h);
                off.toBlob(async (blob) => {
                  if (!blob) { alert('Capture failed'); return; }
                  const fd = new FormData();
                  fd.append('id', idVal);
                  const formEl = document.querySelector('form');
                  const sel = formEl?.querySelector('select[name="category"]');
                  const catVal = sel?.value || 'citizen';
                  fd.append('category', catVal);
                  fd.append('file', blob, `${idVal}-${Date.now()}.jpg`);
                  await fetch(`${API_BASE}/api/register-face`, { method: 'POST', body: fd });
                  triggerAlert(`Captured and registered face for ${idVal}`);
                }, 'image/jpeg', 0.9);
              } catch (e) {
                // ignore
              }
            }} className="w-full bg-green-600 hover:bg-green-700 transition text-white py-2 rounded">Capture current frame</button>
          </form>

          <div className="p-4 bg-white rounded-xl shadow ring-1 ring-slate-200">
            <h2 className="font-semibold mb-2">Alerts</h2>
            <div className="space-y-1 max-h-48 overflow-auto">
              {alerts.map(a => (
                <div key={a.ts} className="text-sm text-red-700">{new Date(a.ts).toLocaleTimeString()} - {a.message}</div>
              ))}
              {alerts.length === 0 && <div className="text-gray-500 text-sm">No alerts</div>}
            </div>
          </div>
        </div>
      </div>

      {soldiers.some(s => s.status === 'critical') && (
        <div className="p-2 bg-red-600 text-white rounded">Critical soldier status detected!</div>
      )}

      <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-4">
        {soldiers.map(s => (
          <div key={s.id} className="p-4 bg-white rounded-xl shadow ring-1 ring-slate-200">
            <div className="font-semibold">{s.id}</div>
            <div className="text-sm">HR: {s.heart_rate} bpm</div>
            <div className="text-sm">GPS: {s.gps?.[0]}, {s.gps?.[1]}</div>
            <div className={`text-sm ${s.status === 'critical' ? 'text-red-700 font-bold' : 'text-gray-700'}`}>Status: {s.status}</div>
          </div>
        ))}
      </div>
    </div>
  );
}


