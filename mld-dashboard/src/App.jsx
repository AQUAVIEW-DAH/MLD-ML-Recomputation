import React, { useEffect, useMemo, useState } from 'react';
import { CircleMarker, MapContainer, Marker, Popup, TileLayer, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { Eye, EyeOff, Waves, Activity, MapPin, Search, Layers, Clock, ShieldAlert } from 'lucide-react';
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

const API_BASE = import.meta.env.VITE_API_BASE || '';
const FETCH_HEADERS = { 'ngrok-skip-browser-warning': 'true' };
const currentCenter = [28.0, -89.0];
const OBS_LEGEND_BINS = [
  { label: '< 15 m', max: 15, color: '#22d3ee' },
  { label: '15-30 m', max: 30, color: '#34d399' },
  { label: '30-45 m', max: 45, color: '#f59e0b' },
  { label: '> 45 m', max: Infinity, color: '#ef4444' },
];
const MODEL_LEGEND_BINS = [
  { label: '< 15 m', max: 15, color: '#0ea5e9' },
  { label: '15-30 m', max: 30, color: '#2563eb' },
  { label: '30-45 m', max: 45, color: '#7c3aed' },
  { label: '> 45 m', max: Infinity, color: '#f97316' },
];
const CORRECTION_LEGEND_BINS = [
  { label: '< -4 m', max: -4, color: '#2563eb' },
  { label: '-4 to -1 m', max: -1, color: '#38bdf8' },
  { label: '-1 to +1 m', max: 1, color: '#e2e8f0' },
  { label: '+1 to +4 m', max: 4, color: '#f59e0b' },
  { label: '> +4 m', max: Infinity, color: '#ef4444' },
];

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

function getValueColor(value, bins, fallback = '#a855f7') {
  if (value == null || Number.isNaN(value)) {
    return fallback;
  }
  return bins.find((bin) => value < bin.max)?.color || bins[bins.length - 1].color;
}

function getObservationColor(mld) {
  return getValueColor(mld, OBS_LEGEND_BINS);
}

function getObservationRangeLabel(mld) {
  return OBS_LEGEND_BINS.find((bin) => mld < bin.max)?.label || OBS_LEGEND_BINS[OBS_LEGEND_BINS.length - 1].label;
}

function getModelColor(mld) {
  return getValueColor(mld, MODEL_LEGEND_BINS);
}

function getModelRangeLabel(mld) {
  return MODEL_LEGEND_BINS.find((bin) => mld < bin.max)?.label || MODEL_LEGEND_BINS[MODEL_LEGEND_BINS.length - 1].label;
}

function getCorrectionColor(delta) {
  return getValueColor(delta, CORRECTION_LEGEND_BINS, '#f8fafc');
}

function getCorrectionRangeLabel(delta) {
  return CORRECTION_LEGEND_BINS.find((bin) => delta < bin.max)?.label || CORRECTION_LEGEND_BINS[CORRECTION_LEGEND_BINS.length - 1].label;
}

function formatObservationTime(isoString) {
  if (!isoString) {
    return 'Unknown time';
  }
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) {
    return isoString;
  }
  return date.toLocaleString();
}

function App() {
  const [metadata, setMetadata] = useState(null);
  const [selectedDate, setSelectedDate] = useState('');
  const [targetPos, setTargetPos] = useState(null);
  const [loading, setLoading] = useState(false);
  const [mldData, setMldData] = useState(null);
  const [error, setError] = useState(null);
  const [modelLayerData, setModelLayerData] = useState(null);
  const [modelLayerLoading, setModelLayerLoading] = useState(false);
  const [modelLayerError, setModelLayerError] = useState(null);
  const [correctionLayerData, setCorrectionLayerData] = useState(null);
  const [correctionLayerLoading, setCorrectionLayerLoading] = useState(false);
  const [correctionLayerError, setCorrectionLayerError] = useState(null);
  const [correctedFieldData, setCorrectedFieldData] = useState(null);
  const [correctedFieldLoading, setCorrectedFieldLoading] = useState(false);
  const [correctedFieldError, setCorrectedFieldError] = useState(null);
  const [allObservationsData, setAllObservationsData] = useState(null);
  const [allObservationsLoading, setAllObservationsLoading] = useState(false);
  const [allObservationsError, setAllObservationsError] = useState(null);
  const [showModelLayer, setShowModelLayer] = useState(true);
  const [showCorrectionLayer, setShowCorrectionLayer] = useState(true);
  const [showCorrectedField, setShowCorrectedField] = useState(false);
  const [showAllObservations, setShowAllObservations] = useState(false);

  useEffect(() => {
    const loadMetadata = async () => {
      try {
        const response = await fetch(`${API_BASE}/metadata`, { headers: FETCH_HEADERS });
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

  useEffect(() => {
    if (!selectedDate) {
      return;
    }

    const loadModelLayer = async () => {
      setModelLayerLoading(true);
      setModelLayerError(null);
      try {
        const timeStr = `${selectedDate}T12:00:00Z`;
        const response = await fetch(`${API_BASE}/map_layer?time=${encodeURIComponent(timeStr)}&layer=model_mld&stride=12`, { headers: FETCH_HEADERS });
        if (!response.ok) {
          throw new Error(`Layer returned ${response.status}`);
        }
        const data = await response.json();
        setModelLayerData(data);
      } catch (err) {
        console.error(err);
        setModelLayerError(err.message);
      } finally {
        setModelLayerLoading(false);
      }
    };

    loadModelLayer();
  }, [selectedDate]);

  useEffect(() => {
    if (!selectedDate) {
      return;
    }

    const loadCorrectionLayer = async () => {
      setCorrectionLayerLoading(true);
      setCorrectionLayerError(null);
      try {
        const timeStr = `${selectedDate}T12:00:00Z`;
        const response = await fetch(`${API_BASE}/map_layer?time=${encodeURIComponent(timeStr)}&layer=correction&stride=12`, { headers: FETCH_HEADERS });
        if (!response.ok) {
          throw new Error(`Correction layer returned ${response.status}`);
        }
        const data = await response.json();
        setCorrectionLayerData(data);
      } catch (err) {
        console.error(err);
        setCorrectionLayerError(err.message);
      } finally {
        setCorrectionLayerLoading(false);
      }
    };

    loadCorrectionLayer();
  }, [selectedDate]);

  useEffect(() => {
    if (!selectedDate) {
      return;
    }

    const loadCorrectedField = async () => {
      setCorrectedFieldLoading(true);
      setCorrectedFieldError(null);
      try {
        const timeStr = `${selectedDate}T12:00:00Z`;
        const response = await fetch(`${API_BASE}/map_layer?time=${encodeURIComponent(timeStr)}&layer=corrected_mld&stride=12`, { headers: FETCH_HEADERS });
        if (!response.ok) {
          throw new Error(`Corrected field returned ${response.status}`);
        }
        const data = await response.json();
        setCorrectedFieldData(data);
      } catch (err) {
        console.error(err);
        setCorrectedFieldError(err.message);
      } finally {
        setCorrectedFieldLoading(false);
      }
    };

    loadCorrectedField();
  }, [selectedDate]);

  useEffect(() => {
    if (!selectedDate) {
      return;
    }

    const loadAllObservations = async () => {
      setAllObservationsLoading(true);
      setAllObservationsError(null);
      try {
        const timeStr = `${selectedDate}T12:00:00Z`;
        const response = await fetch(`${API_BASE}/map_layer?time=${encodeURIComponent(timeStr)}&layer=observations&stride=12`, { headers: FETCH_HEADERS });
        if (!response.ok) {
          throw new Error(`Observation layer returned ${response.status}`);
        }
        const data = await response.json();
        setAllObservationsData(data);
      } catch (err) {
        console.error(err);
        setAllObservationsError(err.message);
      } finally {
        setAllObservationsLoading(false);
      }
    };

    loadAllObservations();
  }, [selectedDate]);

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
        headers: { 'Content-Type': 'application/json', ...FETCH_HEADERS },
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

  const replayReady = Boolean(metadata && selectedDate);
  const nearbyObservations = mldData?.nearby_observations || [];
  const colorCodedObservations = useMemo(
    () => nearbyObservations.map((obs) => ({ ...obs, color: getObservationColor(obs.mld_m), rangeLabel: getObservationRangeLabel(obs.mld_m) })),
    [nearbyObservations],
  );
  const modelLayerPoints = useMemo(
    () => (modelLayerData?.points || []).map((point) => ({ ...point, color: getModelColor(point.value), rangeLabel: getModelRangeLabel(point.value) })),
    [modelLayerData],
  );
  const correctionLayerPoints = useMemo(
    () => (correctionLayerData?.points || []).map((point) => ({ ...point, color: getCorrectionColor(point.value), rangeLabel: getCorrectionRangeLabel(point.value) })),
    [correctionLayerData],
  );
  const correctedFieldPoints = useMemo(
    () => (correctedFieldData?.points || []).map((point) => ({ ...point, color: getModelColor(point.value), rangeLabel: getModelRangeLabel(point.value) })),
    [correctedFieldData],
  );
  const allObservationPoints = useMemo(
    () => (allObservationsData?.points || []).map((point) => ({ ...point, color: getObservationColor(point.value), rangeLabel: getObservationRangeLabel(point.value) })),
    [allObservationsData],
  );

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
            <button
              className="glass-btn"
              type="button"
              onClick={() => setShowModelLayer((prev) => !prev)}
            >
              {showModelLayer ? <EyeOff size={16} /> : <Eye size={16} />}
              {showModelLayer ? 'Hide Model Field' : 'Show Model Field'}
            </button>
            <div className="layer-status-copy">
              {modelLayerLoading && 'Loading sampled model field...'}
              {!modelLayerLoading && modelLayerData && `Model layer points: ${modelLayerData.point_count}`}
              {modelLayerError && `Model layer issue: ${modelLayerError}`}
            </div>
            <button
              className="glass-btn"
              type="button"
              onClick={() => setShowCorrectionLayer((prev) => !prev)}
            >
              {showCorrectionLayer ? <EyeOff size={16} /> : <Eye size={16} />}
              {showCorrectionLayer ? 'Hide Correction Hotspots' : 'Show Correction Hotspots'}
            </button>
            <div className="layer-status-copy">
              {correctionLayerLoading && 'Loading sampled correction field...'}
              {!correctionLayerLoading && correctionLayerData && `Correction points: ${correctionLayerData.point_count}`}
              {correctionLayerError && `Correction layer issue: ${correctionLayerError}`}
            </div>
            <button
              className="glass-btn"
              type="button"
              onClick={() => setShowCorrectedField((prev) => !prev)}
            >
              {showCorrectedField ? <EyeOff size={16} /> : <Eye size={16} />}
              {showCorrectedField ? 'Hide Final Corrected Field' : 'Show Final Corrected Field'}
            </button>
            <div className="layer-status-copy">
              {correctedFieldLoading && 'Loading sampled corrected field...'}
              {!correctedFieldLoading && correctedFieldData && `Corrected field points: ${correctedFieldData.point_count}`}
              {correctedFieldError && `Corrected field issue: ${correctedFieldError}`}
            </div>
            <button
              className="glass-btn"
              type="button"
              onClick={() => setShowAllObservations((prev) => !prev)}
            >
              {showAllObservations ? <EyeOff size={16} /> : <Eye size={16} />}
              {showAllObservations ? 'Hide All In-Situ Points' : 'Show All In-Situ Points'}
            </button>
            <div className="layer-status-copy">
              {allObservationsLoading && 'Loading all replay observations...'}
              {!allObservationsLoading && allObservationsData && `All observations: ${allObservationsData.point_count}`}
              {allObservationsError && `Observation layer issue: ${allObservationsError}`}
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
                  {colorCodedObservations.length} Replay Observations Nearby
                </span>
                {colorCodedObservations.slice(0, 5).map((obs, idx) => (
                  <div
                    key={idx}
                    className="obs-swatch-card"
                    style={{ borderLeftColor: obs.color }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem', gap: '0.75rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span className="obs-legend-dot" style={{ background: obs.color }} />
                        <span style={{ color: 'var(--text-primary)' }}>{obs.source}</span>
                      </div>
                      <span style={{ color: obs.color, fontWeight: 700 }}>{obs.mld_m.toFixed(1)}m</span>
                    </div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                      Range: {obs.rangeLabel} | {obs.distance_km.toFixed(1)} km away
                    </div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '0.2rem' }}>
                      {formatObservationTime(obs.obs_time)}
                    </div>
                  </div>
                ))}
              </div>

              <div className="obs-legend-card">
                <span className="stat-label">Observation MLD Color Ramp</span>
                <div className="obs-legend-grid">
                  {OBS_LEGEND_BINS.map((bin) => (
                    <div key={bin.label} className="obs-legend-item">
                      <span className="obs-legend-dot" style={{ background: bin.color }} />
                      <span>{bin.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              {modelLayerData && (
                <div className="obs-legend-card">
                  <span className="stat-label">Model MLD Field Ramp</span>
                  <div className="obs-legend-grid">
                    {MODEL_LEGEND_BINS.map((bin) => (
                      <div key={bin.label} className="obs-legend-item">
                        <span className="obs-legend-dot" style={{ background: bin.color }} />
                        <span>{bin.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {correctedFieldData && (
                <div className="obs-legend-card">
                  <span className="stat-label">Final Corrected MLD Ramp</span>
                  <div className="obs-legend-grid">
                    {MODEL_LEGEND_BINS.map((bin) => (
                      <div key={bin.label} className="obs-legend-item">
                        <span className="obs-legend-dot" style={{ background: bin.color }} />
                        <span>{bin.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {correctionLayerData && (
                <div className="obs-legend-card">
                  <span className="stat-label">Correction Hotspot Ramp</span>
                  <div className="obs-legend-grid correction-legend-grid">
                    {CORRECTION_LEGEND_BINS.map((bin) => (
                      <div key={bin.label} className="obs-legend-item">
                        <span className="obs-legend-dot" style={{ background: bin.color }} />
                        <span>{bin.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
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

          {showModelLayer && modelLayerPoints.map((point, idx) => (
            <CircleMarker
              key={`model-${idx}`}
              center={[point.lat, point.lon]}
              radius={7}
              pathOptions={{
                color: point.color,
                weight: 0.4,
                fillColor: point.color,
                fillOpacity: 0.28,
              }}
            >
              <Popup>
                <strong>RTOFS Model Field</strong><br />
                Model MLD: {point.value.toFixed(1)}m<br />
                Band: {point.rangeLabel}
              </Popup>
            </CircleMarker>
          ))}

          {showCorrectedField && correctedFieldPoints.map((point, idx) => (
            <CircleMarker
              key={`corrected-${idx}`}
              center={[point.lat, point.lon]}
              radius={6}
              pathOptions={{
                color: point.color,
                weight: 0.5,
                fillColor: point.color,
                fillOpacity: 0.35,
              }}
            >
              <Popup>
                <strong>Final Corrected Field</strong><br />
                Corrected MLD: {point.value.toFixed(1)}m<br />
                Band: {point.rangeLabel}
              </Popup>
            </CircleMarker>
          ))}

          {showCorrectionLayer && correctionLayerPoints.map((point, idx) => (
            <CircleMarker
              key={`correction-${idx}`}
              center={[point.lat, point.lon]}
              radius={4}
              pathOptions={{
                color: point.color,
                weight: 0.8,
                fillColor: point.color,
                fillOpacity: 0.78,
              }}
            >
              <Popup>
                <strong>ML Correction Hotspot</strong><br />
                Correction: {point.value > 0 ? '+' : ''}{point.value.toFixed(1)}m<br />
                Band: {point.rangeLabel}
              </Popup>
            </CircleMarker>
          ))}

          {showAllObservations && allObservationPoints.map((point, idx) => (
            <CircleMarker
              key={`all-obs-${idx}`}
              center={[point.lat, point.lon]}
              radius={5}
              pathOptions={{
                color: '#0f172a',
                weight: 1,
                fillColor: point.color,
                fillOpacity: 0.92,
              }}
            >
              <Popup>
                <strong>{point.source}</strong><br />
                Platform: {point.platform_id || 'unknown'}<br />
                Observed MLD: {point.value.toFixed(1)}m<br />
                Band: {point.rangeLabel}<br />
                Time: {formatObservationTime(point.obs_time)}
              </Popup>
            </CircleMarker>
          ))}

          {targetPos && (
            <Marker position={targetPos} icon={targetIcon}>
              <Popup>
                Query Point<br />
                Lat: {targetPos.lat.toFixed(4)}<br />
                Lon: {targetPos.lng.toFixed(4)}
              </Popup>
            </Marker>
          )}

          {colorCodedObservations.map((obs, idx) => (
            obs.lat != null && obs.lon != null ? (
              <CircleMarker
                key={`obs-${idx}`}
                center={[obs.lat, obs.lon]}
                radius={8}
                pathOptions={{
                  color: '#e2e8f0',
                  weight: 1.5,
                  fillColor: obs.color,
                  fillOpacity: 0.88,
                }}
              >
                <Popup>
                  <strong>{obs.source}</strong><br />
                  Platform: {obs.platform_id || 'unknown'}<br />
                  Observed MLD: {obs.mld_m.toFixed(1)}m<br />
                  Color band: {obs.rangeLabel}<br />
                  Distance: {obs.distance_km.toFixed(1)} km<br />
                  Time: {formatObservationTime(obs.obs_time)}
                </Popup>
              </CircleMarker>
            ) : null
          ))}
        </MapContainer>

        <div className="map-overlay top-left">
          <Clock size={16} />
          <span>{selectedDate || 'Loading date...'}</span>
        </div>

        {showModelLayer && modelLayerPoints.length > 0 && (
          <div className="map-overlay top-right model-map-legend">
            <div className="obs-map-legend-title">Model MLD Field</div>
            {MODEL_LEGEND_BINS.map((bin) => (
              <div key={bin.label} className="obs-legend-item compact">
                <span className="obs-legend-dot" style={{ background: bin.color }} />
                <span>{bin.label}</span>
              </div>
            ))}
          </div>
        )}

        {showCorrectedField && correctedFieldPoints.length > 0 && (
          <div className={`map-overlay ${showModelLayer ? 'upper-mid-right' : 'top-right'} model-map-legend`}>
            <div className="obs-map-legend-title">Final Corrected Field</div>
            {MODEL_LEGEND_BINS.map((bin) => (
              <div key={bin.label} className="obs-legend-item compact">
                <span className="obs-legend-dot" style={{ background: bin.color }} />
                <span>{bin.label}</span>
              </div>
            ))}
          </div>
        )}

        {showCorrectionLayer && correctionLayerPoints.length > 0 && (
          <div className={`map-overlay ${showModelLayer && showCorrectedField ? 'stack-right-2' : showModelLayer || showCorrectedField ? 'lower-right' : 'top-right'} correction-map-legend`}>
            <div className="obs-map-legend-title">Correction Hotspots</div>
            {CORRECTION_LEGEND_BINS.map((bin) => (
              <div key={bin.label} className="obs-legend-item compact">
                <span className="obs-legend-dot" style={{ background: bin.color }} />
                <span>{bin.label}</span>
              </div>
            ))}
          </div>
        )}

        {showAllObservations && allObservationPoints.length > 0 && (
          <div className={`map-overlay ${showModelLayer || showCorrectionLayer || showCorrectedField ? 'stack-right-3' : 'top-right'} obs-map-legend`}>
            <div className="obs-map-legend-title">All Replay In-Situ</div>
            {OBS_LEGEND_BINS.map((bin) => (
              <div key={bin.label} className="obs-legend-item compact">
                <span className="obs-legend-dot" style={{ background: bin.color }} />
                <span>{bin.label}</span>
              </div>
            ))}
          </div>
        )}

        {colorCodedObservations.length > 0 && (
          <div className={`map-overlay ${showAllObservations || showModelLayer || showCorrectionLayer || showCorrectedField ? 'bottom-right' : 'top-right'} obs-map-legend`}>
            <div className="obs-map-legend-title">Observed MLD</div>
            {OBS_LEGEND_BINS.map((bin) => (
              <div key={bin.label} className="obs-legend-item compact">
                <span className="obs-legend-dot" style={{ background: bin.color }} />
                <span>{bin.label}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
