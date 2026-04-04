import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { Waves, Activity, MapPin, Search, Layers, Clock, ShieldAlert } from 'lucide-react';
import './index.css';

// Fix typical Leaflet icon issue in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom icons
const targetIcon = new L.Icon({
  iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const obsIcon = new L.Icon({
  iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [20, 32],
  iconAnchor: [10, 32],
  popupAnchor: [1, -34],
  shadowSize: [32, 32]
});

function MapEventsHandler({ onLocationSelect }) {
  useMapEvents({
    click(e) {
      onLocationSelect(e.latlng);
    },
  });
  return null;
}

function App() {
  const [targetPos, setTargetPos] = useState(null);
  const [loading, setLoading] = useState(false);
  const [mldData, setMldData] = useState(null);
  const [error, setError] = useState(null);

  const fetchMLD = async (latlng) => {
    setLoading(true);
    setTargetPos(latlng);
    setError(null);
    setMldData(null);
    
    try {
      // Hardcode time to the valid RTOFS local slice we know works for demo purposes
      const timeStr = "2026-04-01T06:00:00.000000000";
      
      const response = await fetch('http://127.0.0.1:8000/mld', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          lat: latlng.lat,
          lon: latlng.lng,
          time: timeStr
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

  const currentCenter = [28.0, -89.0]; // Gulf of Mexico

  return (
    <div className="app-container">
      {/* Sidebar Panel */}
      <div className="sidebar">
        <div className="header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <Waves size={28} color="var(--accent-cyan)" />
            <h1 className="title">AQUAVIEW</h1>
          </div>
          <h2 style={{ color: 'var(--text-primary)', fontSize: '1.25rem', marginBottom: '0.25rem' }}>MLD Intelligence</h2>
          <p className="subtitle">
            Hybrid Mix Layer Depth Estimation merging model physics with real-time observation telemetry.
          </p>
        </div>

        {!targetPos && !loading && (
          <div className="instructions">
            <MapPin size={48} />
            <p>Click anywhere in the Gulf of Mexico to generate an intelligent MLD estimate.</p>
          </div>
        )}

        {loading && (
          <div className="instructions">
            <div className="loading-spinner"></div>
            <p>Fusing RTOFS Model with Aquaview Observations...</p>
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
            {/* Primary Result Card */}
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
                  {mldData.confidence} Level
                </span>
              </div>
            </div>

            {/* Provenance Card */}
            <div className="card">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <Layers size={20} color="var(--accent-purple)" />
                Data Provenance
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
              
              <div style={{ marginTop: '1.5rem' }}>
                <span className="stat-label" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <Search size={14} /> 
                  {mldData.nearby_observations.length} Observations Used
                </span>
                
                {mldData.nearby_observations.length > 0 ? (
                  <div className="obs-list">
                    {mldData.nearby_observations.map((obs, idx) => (
                      <div className={`obs-item ${obs.source.toLowerCase()}`} key={idx}>
                        <div className="obs-info">
                          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{obs.source} Platform</span>
                          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                            <Clock size={10} /> {new Date(obs.obs_time).toLocaleDateString()}
                          </span>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <span style={{ display: 'block', fontWeight: 600 }}>{obs.mld_m.toFixed(1)}m</span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{obs.distance_km}km awy</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', marginTop: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                    No observations found within spatial radius. Estimate relies purely on internal model simulation.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Map Interactive Area */}
      <div className="map-container">
        <MapContainer 
          center={currentCenter} 
          zoom={6} 
          style={{ height: '100%', width: '100%' }}
          zoomControl={false}
        >
          {/* Base Map using a sleek dark theme */}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />
          <MapEventsHandler onLocationSelect={fetchMLD} />

          {/* Render Target Click Location */}
          {targetPos && (
            <Marker position={targetPos} icon={targetIcon}>
              <Popup autoPan={false}>
                <b>Query Anchor</b><br />
                {targetPos.lat.toFixed(4)}, {targetPos.lng.toFixed(4)}
              </Popup>
            </Marker>
          )}

          {/* Render Actual Real-time Nearby Observations if present */}
          {mldData && mldData.nearby_observations.map((obs, idx) => {
            // Find lat/lon offset to approximate their location visually since 
            // our API currently didn't return lat/lon specifically for frontend items.
            // In a full implementation we'd pass back precise obs coordinates.
            // Doing a minor visual offset based on distance_km.
            const roughOffset = obs.distance_km / 111.0; 
            return (
              <Marker 
                key={idx} 
                position={[mldData.query_lat + (roughOffset * (idx%2==0?1:-1)), mldData.query_lon + (roughOffset * (idx%2==0?1:-1))]} 
                icon={obsIcon}
              >
                <Popup>
                  <b>{obs.source} Observation</b><br />
                  Measured MLD: {obs.mld_m.toFixed(1)}m<br />
                  Distance: {obs.distance_km}km
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}

export default App;
