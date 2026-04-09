import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { Waves, Activity, MapPin, Search, Layers, Clock, ShieldAlert } from 'lucide-react';
import './index.css';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const targetIcon = new L.Icon({
  iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const obsIcon = new L.Icon({
  iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [20, 32],
  iconAnchor: [10, 32],
  popupAnchor: [1, -34],
  shadowSize: [32, 32],
});

function MapEventsHandler({ onLocationSelect, ready }) {
  useMapEvents({
    click(e) {
      if (ready) {
        onLocationSelect(e.latlng);
      }
    },
  });
  return null;
}

const API_BASE = import.meta.env.VITE_API_BASE || '';

function App() {
  const [metadata, setMetadata] = useState(null);
  const [selectedDate, setSelectedDate] = useState('');
  const [targetPos, setTargetPos] = useState(null);
  const [loading, setLoading] = useState(false);
  const [mldData, setMldData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadMetadata = async () => {
      try {
        const response = await fetch(`${API_BASE}/metadata`);
        if (!response.ok) {
          throw new Error(`Metadata returned ${response.status}`);
        }
        const data = await response.json();
        setMetadata(data);
        if (data.default_query_time) {
          setSelectedDate(data.default_query_time.slice(0, 10));
        } else if (data.available_dates?.length) {
          setSelectedDate(data.available_dates[data.available_dates.length - 1]);
        }
      } catch (err) {
        console.error(err);
        setError(`Failed to load replay metadata${API_BASE ? ` from ${API_BASE}` : ''}: ${err.message}`);
      }
    };
    loadMetadata();
  }, []);

  const fetchMLD = async (latlng) => {
    if (!selectedDate) {
      setError('Choose a replay date before querying the map.');
      return;
    }

    setLoading(true);
    setTargetPos(latlng);
    setError(null);
    setMldData(null);

    try {
      const timeStr = `${selectedDate}T12:00:00Z`;
      const response = await fetch(`${API_BASE}/mld`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat: latlng.lat,
          lon: latlng.lng,
          time: timeStr,
        }),
      });

      if (!response.ok) {
        throw new Error(`API returned ${response.status}: ${await response.text()}`);
      }

      const data = await response.json();
      setMldData(data);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const currentCenter = [28.0, -89.0];
  const replayReady = Boolean(metadata && selectedDate);

  return (
    <div className="app-container">
      <div className="sidebar">
        <div className="header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <Waves size={28} color="var(--accent-cyan)" />
            <h1 className="title">MLD Replay</h1>
          </div>
          <h2 style={{ color: 'var(--text-primary)', fontSize: '1.25rem', marginBottom: '0.25rem' }}>Historical Sandbox</h2>
          <p className="subtitle">
            Frozen Jul-Aug 2025 replay using same-day RTOFS files, the historical replay model, and local holdout observations for provenance.
          </p>
        </div>

        {metadata && (
          <div className="card">
            <h3 style={{ marginBottom: '1rem' }}>Replay Controls</h3>
            <div className="stat-grid">
              <div className="stat-item">
                <span className="stat-label">Mode</span>
                <span className="stat-value" style={{ fontSize: '1rem' }}>{metadata.mode}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Available Dates</span>
                <span className="stat-value" style={{ fontSize: '1rem' }}>{metadata.available_date_count}</span>
              </div>
            </div>
            <div style={{ marginTop: '1rem' }}>
              <label className="stat-label" htmlFor="replay-date">Replay Date</label>
              <select
                id="replay-date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                style={{
                  marginTop: '0.5rem',
                  width: '100%',
                  padding: '0.75rem',
                  borderRadius: '10px',
                  background: 'rgba(15, 23, 42, 0.85)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-color)',
                }}
              >
                {metadata.available_dates?.map((date) => (
                  <option key={date} value={date}>{date}</option>
                ))}
              </select>
            </div>
            <div style={{ marginTop: '1rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Support window: {metadata.support_radius_km} km / {metadata.support_window_hr} hr
            </div>
          </div>
        )}

        {!targetPos && !loading && (
          <div className="instructions">
            <MapPin size={48} />
            <p>
              {replayReady
                ? 'Choose a replay date, then click anywhere in the Gulf of Mexico to query the historical sandbox.'
                : 'Loading replay metadata and date controls...'}
            </p>
          </div>
        )}

        {loading && (
          <div className="instructions">
            <div className="loading-spinner"></div>
            <p>Querying historical replay sandbox...</p>
          </div>
        )}

        {error && (
          <div className="card" style={{ borderLeft: '4px solid var(--danger)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <ShieldAlert color="var(--danger)" size={20} />
              <h3 style={{ color: 'var(--danger)' }}>Query Failed</h3>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{error}</p>
          </div>
        )}

        {mldData && !loading && (
          <div className="results-container">
            <div className="card">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <Activity size={20} color="var(--accent-cyan)" />
                Best Estimate
              </h3>

              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '3.5rem', fontWeight: '800', lineHeight: 1, letterSpacing: '-0.02em', background: 'linear-gradient(to right, #fff, #a5b4fc)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                  {mldData.best_estimate_mld.toFixed(1)}
                </span>
                <span style={{ color: 'var(--text-secondary)', fontSize: '1.2rem' }}>meters</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '1rem', marginTop: '1rem' }}>
                <span className="stat-label">Confidence</span>
                <span className={`badge badge-${mldData.confidence.toLowerCase()}`}>
                  {mldData.confidence}
                </span>
              </div>
            </div>

            <div className="card">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <Layers size={20} color="var(--accent-purple)" />
                Provenance
              </h3>

              <div className="stat-grid">
                <div className="stat-item">
                  <span className="stat-label">Model (RTOFS)</span>
                  <span className="stat-value">{mldData.model_mld.toFixed(1)}m</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Correction</span>
                  <span className={`stat-value ${mldData.correction_applied !== 0 ? 'highlight' : ''}`}>
                    {mldData.correction_applied > 0 ? '+' : ''}{mldData.correction_applied.toFixed(1)}m
                  </span>
                </div>
              </div>

              <div style={{ marginTop: '1rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Replay date: {selectedDate} | Observation mode: {mldData.window_used}
              </div>

              <div style={{ marginTop: '1.5rem' }}>
                <span className="stat-label" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <Search size={14} />
                  {mldData.nearby_observations.length} Replay Observations Nearby
                </span>
                {mldData.nearby_observations.slice(0, 5).map((obs, idx) => (
                  <div key={idx} style={{
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: '10px',
                    padding: '0.75rem',
                    marginTop: '0.5rem',
                    fontSize: '0.85rem'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <span style={{ color: 'var(--text-primary)' }}>{obs.source}</span>
                      <span style={{ color: 'var(--accent-cyan)' }}>{obs.mld_m.toFixed(1)}m</span>
                    </div>
                    <div style={{ color: 'var(--text-secondary)' }}>
                      {obs.distance_km.toFixed(1)} km away | {obs.obs_time}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="map-container">
        <MapContainer center={currentCenter} zoom={6} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          <MapEventsHandler onLocationSelect={fetchMLD} ready={replayReady} />

          {targetPos && (
            <Marker position={targetPos} icon={targetIcon}>
              <Popup>
                Query Point<br />
                Lat: {targetPos.lat.toFixed(4)}<br />
                Lon: {targetPos.lng.toFixed(4)}
              </Popup>
            </Marker>
          )}

          {mldData?.nearby_observations?.map((obs, idx) => (
            obs.lat != null && obs.lon != null ? (
              <Marker key={idx} position={[obs.lat, obs.lon]} icon={obsIcon}>
                <Popup>
                  <strong>{obs.source}</strong><br />
                  Platform: {obs.platform_id || 'unknown'}<br />
                  Observed MLD: {obs.mld_m.toFixed(1)}m<br />
                  Distance: {obs.distance_km.toFixed(1)} km<br />
                  Time: {obs.obs_time}
                </Popup>
              </Marker>
            ) : null
          ))}
        </MapContainer>

        <div className="map-overlay top-left">
          <Clock size={16} />
          <span>{selectedDate || 'Loading date...'}</span>
        </div>
      </div>
    </div>
  );
}

export default App;
