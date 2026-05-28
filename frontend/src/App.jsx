import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, CircleMarker, Tooltip, useMapEvents, useMap } from 'react-leaflet';
import { MapPin, Navigation, Clock, Bot, Send, Layers, Play, Square, FastForward, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import L from 'leaflet';
import './index.css';

// Fix for default marker icons in Leaflet
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

const MAP_STYLES = {
  light: "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
  satellite: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
};

const LOCATIONS = [
  // Transit Stops (from GeoJSON — verified coords)
  "Abhayankar nagar bus stop", "Agrasen Square", "Airport", "Airport South", "Ajni", "Ajni Square",
  "Ambazari Lake", "Ambedkar Square", "Automotive Square", "Aychit Mandir Bus Stop", "Ayodhya T-point",
  "Bamhni", "Bansi Nagar", "Bharatwada", "Bhiwapur", "Borkhedi",
  "Bus Stop Hatodi", "Bus Stop Khaparkheda", "Bus Stop Barshi", "Bus Stop Dudhala",
  "Bus Stop Lohdongri", "Bus Stop Lohdongri Camp", "Bus Stop Nimkheda", "Bus Stop Sangrampur",
  "Buti Bori", "Bypass Bus Stand", "Chacher", "Chhatrapati Square", "Chitaroli Square", "Chitroli Square",
  "Congress Nagar", "Cotton Market", "Dighori Buzurg", "Dosar Vaisya Square",
  "Dr. Babasaheb Ambedkar International Airport", "Friends Colony Bus Stop",
  "Futala Lake", "GMC", "Gaddi Godam Square", "Godhani", "Gorewada Zoo", "Gumgaon",
  "Indora Square", "Institute of Engineers", "Itwari Junction", "Jaiprakash Nagar",
  "Jhasi Rani Square", "Kadvi Square", "Kalamna", "Kalmeshwar", "Kalmeshwar Bus Stand MSRTC",
  "Kamptee", "Kamptee MSRTC Bus Stand", "Kanhan Junction", "Kapri Kheda",
  "Kasturchand Park", "Khapa Bus Stand", "Khapri", "Khurana", "Kohli", "Koradi Naka", "Kuhi",
  "LAD College", "Lokmanya Nagar", "Metpanjra", "Mhalgi Nagar Square",
  "Nagpur Junction", "Nagpur Railway Station", "Nari Road", "New Airport", "Nimkheda Bus Stop",
  "Pachgav Bus Stop", "Panjara", "Parshivani Msrtc Bus Stand", "Patansaongi",
  "Prajapati Nagar", "Rachna Ring Road", "Rahate Colony", "Ramtek", "Rewral",
  "ST Bus Depot", "SVPCET", "Salwa", "Sanjay Gandhi Nagar", "Saoner Bus Stand", "Saoner Junction",
  "Seloo Road", "Seminary Hills", "Shankar Nagar Square", "Sindi",
  "Sitabuldi", "Sitabuldi City Bus Stand", "Sitabuldi Fort", "Sonkhamb",
  "Subhash Nagar", "Takli Bansali P.H.", "Telephone Exchange", "Tharsa", "Tuljapur",
  "Ujjwal Nagar", "Umred", "Umred Colliery Siding", "VNIT",
  "Vaishnodevi Square", "Vasudev Nagar", "Vayusena Nagar",
  "Waroda Bus Stop", "Waygaon", "Zaveri Nursing Home, Nagpur", "Zero Mile", "Zero Mile Stone",
  // Colleges & Universities
  "AIIMS Nagpur", "Deekshabhoomi", "Dharampeth Science College", "G. S. College of Commerce",
  "G.H. Raisoni College of Engineering", "Hislop College", "Institute of Science",
  "KDK College", "LAD College", "Nagpur University (RTM)", "Priyadarshini College of Engineering",
  "RKNEC", "Ramdeobaba College of Engineering", "Symbiosis International University", "YCCE",
  // Hospitals
  "Alexis Hospital", "Kingsway Hospital", "KIMS Kingsway Hospital",
  "Lata Mangeshkar Hospital", "Mayo Hospital (IGGMCH)", "Orange City Hospital", "Wockhardt Hospital",
  // Malls & Landmarks
  "Empress Mall", "Eternity Mall", "Lokmat Square Mall", "Maharaj Bagh Zoo", "Raman Science Centre",
  // Neighbourhoods & Areas
  "Bhandara Road", "Byramji Town", "Civil Lines", "Dharampeth", "Dharampeth Square",
  "Fetri", "Gandhibagh", "Gittikhadan", "Gondkhairi",
  "Hingna", "Itwari", "Jamtha", "Jaripatka", "Law College Square",
  "Laxmi Nagar Square", "Manish Nagar", "Medical Square", "Medical College Square",
  "Nandanvan", "Pardi", "Pratap Nagar", "Ramdaspeth", "Reshimbagh",
  "Sadar", "Shankar Nagar", "Sonegaon", "Takalghat", "Trimurti Nagar",
  "Wardhaman Nagar", "Wardhaman Nagar Square", "Wathoda"
].sort((a, b) => a.localeCompare(b));

function AutocompleteInput({ value, onChange, placeholder, icon: Icon, color, locations }) {
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef(null);

  const filtered = locations.filter(loc => 
    loc.toLowerCase().includes(value.toLowerCase())
  );

  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [wrapperRef]);

  return (
    <div className="input-field" style={{ position: 'relative' }} ref={wrapperRef}>
      <Icon size={18} color={color} />
      <input 
        type="text" 
        placeholder={placeholder} 
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
      />
      {isOpen && filtered.length > 0 && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          background: 'white',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          maxHeight: '160px',
          overflowY: 'auto',
          zIndex: 2000,
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          marginTop: '4px'
        }}>
          {filtered.map((loc, idx) => (
            <div 
              key={idx}
              onClick={() => {
                onChange(loc);
                setIsOpen(false);
              }}
              style={{
                padding: '0.6rem 0.8rem',
                cursor: 'pointer',
                borderBottom: idx === filtered.length - 1 ? 'none' : '1px solid #f3f4f6',
                fontSize: '0.85rem',
                color: '#374151'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#f3f4f6'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
            >
              {loc}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ZoomHandler({ setZoomLevel }) {
  useMapEvents({
    zoomend: (e) => {
      setZoomLevel(e.target.getZoom());
    }
  });
  return null;
}

function RouteFitBounds({ routeData }) {
  const map = useMap();
  useEffect(() => {
    if (routeData && routeData.segments && routeData.segments.length > 0) {
      const allCoords = [];
      routeData.segments.forEach(seg => {
        seg.coordinates.forEach(coord => {
          allCoords.push(coord);
        });
      });
      if (allCoords.length > 0) {
        const bounds = L.latLngBounds(allCoords);
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 16 });
      }
    }
  }, [routeData, map]);
  return null;
}

function App() {
  // Session ID for chatbot state history
  const [sessionId] = useState(() => Math.random().toString(36).substring(2, 9));
  
  const [mapStyle, setMapStyle] = useState('light');
  const [isPeakHour, setIsPeakHour] = useState(false);
  const [travelMode, setTravelMode] = useState('all'); // 'all', 'path'
  const [chatOpen, setChatOpen] = useState(false);
  const [messages, setMessages] = useState([
    { sender: 'bot', text: "Namaste! I am V-NEURON's Agentic Navigation Assistant. Let me know where you want to travel in Nagpur!" }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [source, setSource] = useState('');
  const [destination, setDestination] = useState('');
  const [routeData, setRouteData] = useState(null);
  const [loadingRoute, setLoadingRoute] = useState(false);
  const [mapMarkers, setMapMarkers] = useState([]);
  const [zoomLevel, setZoomLevel] = useState(13);

  // Merge hardcoded locations with backend markers
  const allLocations = React.useMemo(() => {
    const locSet = new Set(LOCATIONS);
    mapMarkers.forEach(m => locSet.add(m.name));
    return Array.from(locSet).sort((a, b) => a.localeCompare(b));
  }, [mapMarkers]);

  // Live Simulation state
  const [simCoords, setSimCoords] = useState([]);
  const [simCoordsMeta, setSimCoordsMeta] = useState([]);
  const [simIndex, setSimIndex] = useState(0);
  const [simPosition, setSimPosition] = useState(null);
  const [simSpeedMultiplier, setSimSpeedMultiplier] = useState(1);
  const [simulating, setSimulating] = useState(false);
  const [simTelemetry, setSimTelemetry] = useState({
    speed: 0,
    mode: '',
    distanceLeft: 0,
    timeLeft: 0
  });

  const simulationIntervalRef = useRef(null);
  const chatEndRef = useRef(null);
  const isFirstRender = useRef(true);

  // Fetch markers on component mount
  useEffect(() => {
    fetch('http://localhost:8000/markers')
      .then(res => res.json())
      .then(data => {
        if (data.markers) setMapMarkers(data.markers);
      })
      .catch(err => console.error("Error fetching markers:", err));
  }, []);

  // Sync simulation coordinates when route changes
  useEffect(() => {
    if (routeData && routeData.segments) {
      const coordsList = [];
      const metaList = [];
      routeData.segments.forEach(seg => {
        seg.coordinates.forEach(coord => {
          coordsList.push(coord);
          metaList.push({
            highway: seg.highway,
            distance_m: seg.distance_m,
            travel_time_s: seg.travel_time_s
          });
        });
      });
      setSimCoords(coordsList);
      setSimCoordsMeta(metaList);
      setSimIndex(0);
      setSimPosition(null);
      setSimulating(false);
      if (simulationIntervalRef.current) {
        clearInterval(simulationIntervalRef.current);
      }
    }
  }, [routeData]);

  // Clean up interval on unmount
  useEffect(() => {
    return () => {
      if (simulationIntervalRef.current) clearInterval(simulationIntervalRef.current);
    };
  }, []);

  // Autoscroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, chatOpen]);

  // Nagpur coordinates center
  const center = [21.1458, 79.0882];

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMessage = chatInput.trim();
    setMessages(prev => [...prev, { sender: 'user', text: userMessage }]);
    setChatInput('');

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: userMessage,
          session_id: sessionId
        })
      });

      if (!response.ok) throw new Error("Server communication issue");

      const data = await response.json();
      
      // Update assistant reply
      setMessages(prev => [...prev, { sender: 'bot', text: data.reply }]);

      // Dynamically snap parameters returned by Agentic match on backend
      if (data.source) setSource(data.source);
      if (data.destination) setDestination(data.destination);
      if (data.isPeakHour !== undefined && data.isPeakHour !== null) setIsPeakHour(data.isPeakHour);
      if (data.travelMode) setTravelMode(data.travelMode);
      if (data.routeData) setRouteData(data.routeData);

    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { sender: 'bot', text: `Sorry, I couldn't reach the backend: ${error.message}` }]);
    }
  };

  const calculateRoute = async () => {
    if (!source || !destination) {
      alert("Please select both source and destination!");
      return;
    }
    
    setLoadingRoute(true);
    setRouteData(null);
    
    try {
      const response = await fetch('http://localhost:8000/route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source,
          destination,
          isPeakHour,
          travelMode
        })
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to fetch route');
      }

      const data = await response.json();
      setRouteData(data);
      
      setMessages(prev => [...prev, { 
        sender: 'bot', 
        text: `Calculated multimodal path. Distance: ${data.metrics.distance_km} km. Travel time: ${data.metrics.time_min} mins.` 
      }]);

    } catch (error) {
      console.error(error);
      alert(error.message);
    } finally {
      setLoadingRoute(false);
    }
  };

  // Auto-recalculate route when mode or time changes
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    if (source && destination) {
      calculateRoute();
    }
  }, [travelMode, isPeakHour]);

  // Run/Control animated vehicle tracking simulation
  const startSimulation = (multiplier = simSpeedMultiplier) => {
    if (simCoords.length === 0) return;
    setSimulating(true);
    setSimSpeedMultiplier(multiplier);
    
    if (simulationIntervalRef.current) clearInterval(simulationIntervalRef.current);
    
    let currentIndex = simIndex;
    
    const step = () => {
      if (currentIndex >= simCoords.length) {
        clearInterval(simulationIntervalRef.current);
        setSimulating(false);
        setSimPosition(null);
        setSimIndex(0);
        return;
      }
      
      setSimIndex(currentIndex);
      setSimPosition(simCoords[currentIndex]);
      
      const meta = simCoordsMeta[currentIndex] || {};
      const mode = meta.highway || 'road';
      
      let baseSpeed = 40;
      if (mode.includes('subway')) baseSpeed = 55;
      else if (mode.includes('footway')) baseSpeed = 5;
      else if (isPeakHour) baseSpeed = 12;
      
      const remainingFraction = (simCoords.length - 1 - currentIndex) / (simCoords.length - 1 || 1);
      const distanceLeft = (routeData.metrics.distance_km * remainingFraction).toFixed(2);
      const timeLeft = Math.round(routeData.metrics.time_min * remainingFraction);
      
      setSimTelemetry({
        speed: baseSpeed,
        mode: mode.includes('subway') ? '🚇 Metro' : mode.includes('footway') ? '🚶 Walking' : '🚗 Driving',
        distanceLeft: parseFloat(distanceLeft) > 0 ? distanceLeft : '0.00',
        timeLeft: timeLeft > 0 ? timeLeft : 0
      });
      
      currentIndex += 1;
    };

    step();
    // Stepping delay scaled inversely by playback multiplier
    simulationIntervalRef.current = setInterval(step, 300 / multiplier);
  };

  const pauseSimulation = () => {
    setSimulating(false);
    if (simulationIntervalRef.current) clearInterval(simulationIntervalRef.current);
  };

  const stopSimulation = () => {
    setSimulating(false);
    setSimPosition(null);
    setSimIndex(0);
    if (simulationIntervalRef.current) clearInterval(simulationIntervalRef.current);
  };

  const getModeColor = (highway, style) => {
    const h = String(highway).toLowerCase();
    if (h.includes("subway")) return "#ea580c";
    if (h.includes("footway")) return "#10b981";
    if (h.includes("primary")) return "#3b82f6";
    return "#2563eb";
  };

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative', overflow: 'hidden' }}>
      
      {/* Background Leaflet Map */}
      <MapContainer 
        center={center} 
        zoom={13} 
        zoomControl={false} 
        className="map-container"
        zoomSnap={0.5}
        wheelPxPerZoomLevel={120}
        bounceAtZoomLimits={false}
      >
        <ZoomHandler setZoomLevel={setZoomLevel} />
        <RouteFitBounds routeData={routeData} />
        <TileLayer
          url={MAP_STYLES[mapStyle]}
          attribution='&copy; OpenStreetMap contributors'
        />
        
        {/* Origin Marker */}
        {routeData && routeData.origin_coords && (
          <CircleMarker
            center={routeData.origin_coords}
            radius={11}
            pathOptions={{ color: '#16a34a', fillColor: '#4ade80', fillOpacity: 1, weight: 3 }}
          >
            <Popup><strong>🟢 Start</strong><br/>{routeData.source}</Popup>
            <Tooltip direction="top" offset={[0, -13]} permanent opacity={0.95}>
              <span style={{ fontWeight: 700, fontSize: '0.75rem', color: '#15803d' }}>📍 {routeData.source}</span>
            </Tooltip>
          </CircleMarker>
        )}

        {/* Destination Marker */}
        {routeData && routeData.destination_coords && (
          <CircleMarker
            center={routeData.destination_coords}
            radius={11}
            pathOptions={{ color: '#dc2626', fillColor: '#f87171', fillOpacity: 1, weight: 3 }}
          >
            <Popup><strong>🔴 End</strong><br/>{routeData.destination}</Popup>
            <Tooltip direction="top" offset={[0, -13]} permanent opacity={0.95}>
              <span style={{ fontWeight: 700, fontSize: '0.75rem', color: '#b91c1c' }}>🏁 {routeData.destination}</span>
            </Tooltip>
          </CircleMarker>
        )}

        {/* Route Polyline Segments */}
        {routeData && routeData.segments && routeData.segments.map((seg, idx) => (
          <Polyline
            key={idx}
            positions={seg.coordinates}
            color={getModeColor(seg.highway, mapStyle)}
            weight={6}
            opacity={0.85}
          >
            <Popup>Mode: {seg.highway} <br/> Time: {(seg.travel_time_s / 60).toFixed(1)} mins</Popup>
          </Polyline>
        ))}

        {/* Mode-Change Waypoint Markers */}
        {routeData && routeData.segments && (() => {
          const waypoints = [];
          const segs = routeData.segments;
          for (let i = 1; i < segs.length; i++) {
            const prevMode = String(segs[i - 1].highway).toLowerCase();
            const currMode = String(segs[i].highway).toLowerCase();
            // Only mark where the transit mode actually changes
            if (prevMode === currMode) continue;
            const coord = segs[i].coordinates[0];
            if (!coord) continue;

            const isMetroSwitch = currMode.includes('subway') || prevMode.includes('subway');
            const isWalkSwitch = currMode.includes('footway') || prevMode.includes('footway');
            const bgColor = isMetroSwitch ? '#ea580c' : isWalkSwitch ? '#10b981' : '#6366f1';
            const emoji = isMetroSwitch ? '🚇' : isWalkSwitch ? '🚶' : '🔄';
            const fromLabel = prevMode.includes('subway') ? 'Metro' : prevMode.includes('footway') ? 'Walk' : 'Road';
            const toLabel = currMode.includes('subway') ? 'Metro' : currMode.includes('footway') ? 'Walk' : 'Road';

            waypoints.push(
              <CircleMarker
                key={`wp-${i}`}
                center={coord}
                radius={8}
                pathOptions={{ color: bgColor, fillColor: '#ffffff', fillOpacity: 1, weight: 2.5 }}
              >
                <Popup>
                  <strong>{emoji} Mode Change</strong><br/>
                  {fromLabel} → {toLabel}
                </Popup>
                <Tooltip direction="top" offset={[0, -10]} opacity={0.97}>
                  <div style={{ textAlign: 'center' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.75rem' }}>{emoji} {fromLabel} → {toLabel}</span>
                  </div>
                </Tooltip>
              </CircleMarker>
            );
          }
          return waypoints;
        })()}


        {/* Live Simulation Animating Marker */}
        {simPosition && (
          <CircleMarker 
            center={simPosition}
            radius={9}
            pathOptions={{
              color: '#ef4444',
              fillColor: '#fecaca',
              fillOpacity: 0.9,
              weight: 3
            }}
          >
            <Popup>
              <strong>Simulated Vehicle</strong><br/>
              Speed: {simTelemetry.speed} km/h<br/>
              Mode: {simTelemetry.mode}
            </Popup>
            <Tooltip permanent direction="right" offset={[10, 0]}>
              <span style={{ fontWeight: 700, color: '#b91c1c' }}>Live Tracking</span>
            </Tooltip>
          </CircleMarker>
        )}

        {/* Dynamic Transit stops rendering */}
        {mapMarkers.map((marker, idx) => {
          const isMetro = marker.type === 'metro';

          // Metro visible from zoom 11, bus stops from zoom 13
          if (isMetro && zoomLevel < 11) return null;
          if (!isMetro && zoomLevel < 13) return null;

          const color = isMetro ? '#ea580c' : '#0284c7';
          const fillColor = isMetro ? '#ffedd5' : '#e0f2fe';
          const label = isMetro ? '🚇 Metro' : '🚌 Bus Stop';

          let radius = isMetro ? 7 : 5;
          if (zoomLevel < 13) radius = isMetro ? 5 : 3;
          else if (zoomLevel >= 16) radius = isMetro ? 10 : 7;

          return (
            <CircleMarker
              key={marker.id || idx}
              center={marker.position}
              radius={radius}
              pathOptions={{
                color: color,
                fillColor: fillColor,
                fillOpacity: 0.9,
                weight: isMetro ? 2.5 : 1.5
              }}
            >
              <Tooltip direction="top" offset={[0, -radius - 2]} opacity={1}>
                <div style={{ textAlign: 'center', lineHeight: '1.4' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.82rem', color: '#1e293b' }}>{marker.name}</span>
                  <br/>
                  <span style={{
                    fontSize: '0.68rem',
                    fontWeight: 600,
                    color: isMetro ? '#ea580c' : '#0284c7',
                    background: isMetro ? '#fff7ed' : '#e0f2fe',
                    padding: '1px 5px',
                    borderRadius: '4px'
                  }}>{label}</span>
                </div>
              </Tooltip>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {/* Map Tile Overlay Controls */}
      <div className="map-controls">
        <button 
          className={mapStyle === 'light' ? 'active' : ''} 
          onClick={() => setMapStyle('light')}
          title="Light Map"
        >
          <Layers size={18} />
        </button>
        <button 
          className={mapStyle === 'satellite' ? 'active' : ''} 
          onClick={() => setMapStyle('satellite')}
          title="Satellite Map"
        >
          <MapPin size={18} />
        </button>
      </div>

      {/* Left Navigation Console */}
      <div className="floating-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ background: '#3b82f6', color: 'white', borderRadius: '8px', padding: '0.4rem' }}>
            <Navigation size={22} />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#1e3a8a' }}>V-NEURON</h2>
            <p style={{ margin: 0, fontSize: '0.75rem', color: '#6b7280' }}>Multimodal Routing Console</p>
          </div>
        </div>
        
        <div className="input-group">
          <AutocompleteInput 
            value={source}
            onChange={setSource}
            placeholder="Starting Point..."
            icon={MapPin}
            color="#ef4444"
            locations={allLocations}
          />
          <AutocompleteInput 
            value={destination}
            onChange={setDestination}
            placeholder="Destination..."
            icon={Navigation}
            color="#3b82f6"
            locations={allLocations}
          />
        </div>

        <div>
          <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#4b5563' }}>TIME SCENARIO</label>
          <div className="options-row">
            <button 
              className={`toggle-btn ${!isPeakHour ? 'active' : ''}`}
              onClick={() => setIsPeakHour(false)}
            >
              🟢 Off-Peak
            </button>
            <button 
              className={`toggle-btn ${isPeakHour ? 'active' : ''}`}
              onClick={() => setIsPeakHour(true)}
            >
              🔴 Peak Hour
            </button>
          </div>
        </div>

        <div>
          <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#4b5563' }}>TRAVEL MODE</label>
          <div className="options-row">
            <button 
              className={`toggle-btn ${travelMode === 'all' ? 'active' : ''}`}
              onClick={() => setTravelMode('all')}
            >
              All Modes
            </button>
            <button 
              className={`toggle-btn ${travelMode === 'path' ? 'active' : ''}`}
              onClick={() => setTravelMode('path')}
            >
              Road Only
            </button>
          </div>
        </div>

        <button className="primary-btn" onClick={calculateRoute} disabled={loadingRoute}>
          {loadingRoute ? 'Finding Path...' : 'Calculate Route'}
        </button>

        {/* Route summary information */}
        {routeData && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ borderTop: '1px solid #f3f4f6', paddingTop: '1rem' }}
          >
            <h3 style={{ fontSize: '0.85rem', fontWeight: 800, margin: '0 0 0.5rem', color: '#374151' }}>ROUTE DETAILS</h3>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
              <div>
                <span style={{ fontSize: '0.7rem', color: '#6b7280', display: 'block' }}>Distance</span>
                <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>{routeData.metrics.distance_km} km</span>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: '#6b7280', display: 'block' }}>Time</span>
                <span style={{ fontWeight: 700, fontSize: '1.1rem', color: '#ef4444' }}>{routeData.metrics.time_min} mins</span>
              </div>
            </div>
            
            <div>
              <span style={{ fontSize: '0.7rem', color: '#6b7280', display: 'block', marginBottom: '0.35rem' }}>Transportation Modes</span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                {Array.from(new Set(routeData.segments.map(s => s.highway))).map(mode => {
                   let label = "🚗 Road";
                   let bgColor = "#eff6ff";
                   let color = "#3b82f6";
                   const m = String(mode).toLowerCase();
                   if (m.includes('subway')) { label = "🚇 Metro"; bgColor = "#fff7ed"; color = "#ea580c"; }
                   else if (m.includes('footway') || m.includes('pedestrian') || m.includes('path')) { label = "🚶 Walk"; bgColor = "#ecfdf5"; color = "#10b981"; }
                   
                   return (
                     <span key={mode} style={{ 
                       background: bgColor, color, 
                       padding: '0.25rem 0.5rem', 
                       borderRadius: '6px', 
                       fontSize: '0.7rem', 
                       fontWeight: 700 
                     }}>
                       {label}
                     </span>
                   )
                })}
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Floating Interactive Live Telemetry / Simulation Panel */}
      <AnimatePresence>
        {routeData && simCoords.length > 0 && (
          <motion.div 
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            style={{
              position: 'absolute',
              bottom: '20px',
              left: '20px',
              width: '380px',
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(8px)',
              borderRadius: '16px',
              boxShadow: '0 10px 30px rgba(0,0,0,0.15)',
              padding: '1.25rem',
              zIndex: 1000,
              border: '1px solid rgba(255, 255, 255, 0.3)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <span style={{ fontWeight: 800, fontSize: '0.85rem', color: '#1e40af', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <Clock size={16} className={simulating ? 'animate-pulse' : ''} />
                ROUTE TRACKING SIMULATOR
              </span>
              {simulating && (
                <span style={{ background: '#fee2e2', color: '#ef4444', fontSize: '0.65rem', fontWeight: 800, padding: '0.15rem 0.4rem', borderRadius: '4px', animation: 'pulse 1.5s infinite' }}>
                  SIMULATING
                </span>
              )}
            </div>

            {/* Sim Control Controls */}
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
              {!simulating ? (
                <button 
                  onClick={() => startSimulation(simSpeedMultiplier)}
                  style={{ flex: 1, background: '#10b981', color: 'white', border: 'none', padding: '0.6rem', borderRadius: '8px', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.25rem' }}
                >
                  <Play size={16} fill="white" />
                  {simIndex > 0 ? 'Resume' : 'Start tracking'}
                </button>
              ) : (
                <button 
                  onClick={pauseSimulation}
                  style={{ flex: 1, background: '#f59e0b', color: 'white', border: 'none', padding: '0.6rem', borderRadius: '8px', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.25rem' }}
                >
                  <Square size={16} fill="white" />
                  Pause
                </button>
              )}
              <button 
                onClick={stopSimulation}
                disabled={simIndex === 0 && !simulating}
                style={{ background: '#ef4444', color: 'white', border: 'none', padding: '0.6rem', borderRadius: '8px', fontWeight: 700, cursor: 'pointer', opacity: (simIndex === 0 && !simulating) ? 0.5 : 1 }}
              >
                Reset
              </button>
            </div>

            {/* Telemetry Multipliers */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem', fontSize: '0.75rem' }}>
              <span style={{ color: '#4b5563', fontWeight: 600 }}>Simulation speed:</span>
              <div style={{ display: 'flex', gap: '0.25rem' }}>
                {[1, 2, 5, 10].map(mult => (
                  <button 
                    key={mult}
                    onClick={() => {
                      setSimSpeedMultiplier(mult);
                      if (simulating) startSimulation(mult);
                    }}
                    style={{
                      background: simSpeedMultiplier === mult ? '#3b82f6' : '#e5e7eb',
                      color: simSpeedMultiplier === mult ? 'white' : '#4b5563',
                      border: 'none',
                      padding: '0.25rem 0.5rem',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontWeight: 700
                    }}
                  >
                    {mult}x
                  </button>
                ))}
              </div>
            </div>

            {/* Simulating Progress Bar */}
            <div style={{ background: '#e5e7eb', height: '6px', borderRadius: '3px', overflow: 'hidden', marginBottom: '1rem' }}>
              <div 
                style={{ 
                  background: '#3b82f6', 
                  height: '100%', 
                  width: `${(simIndex / (simCoords.length - 1 || 1)) * 100}%`,
                  transition: 'width 0.2s linear'
                }}
              />
            </div>

            {/* Live Telemetry Display */}
            {simPosition && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', background: '#f3f4f6', padding: '0.75rem', borderRadius: '8px', fontSize: '0.8rem' }}
              >
                <div>
                  <span style={{ color: '#6b7280', fontSize: '0.7rem', display: 'block' }}>Speed</span>
                  <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>{simTelemetry.speed} km/h</span>
                </div>
                <div>
                  <span style={{ color: '#6b7280', fontSize: '0.7rem', display: 'block' }}>Transit Mode</span>
                  <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#2563eb' }}>{simTelemetry.mode}</span>
                </div>
                <div>
                  <span style={{ color: '#6b7280', fontSize: '0.7rem', display: 'block' }}>Distance to Go</span>
                  <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>{simTelemetry.distanceLeft} km</span>
                </div>
                <div>
                  <span style={{ color: '#6b7280', fontSize: '0.7rem', display: 'block' }}>ETA Countdown</span>
                  <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#ef4444' }}>{simTelemetry.timeLeft} mins</span>
                </div>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating Conversational AI Agent Sidepanel */}
      <div className="floating-chat" style={{ height: chatOpen ? '380px' : '50px', transition: 'height 0.3s ease-in-out' }}>
        <div 
          className="chat-header" 
          onClick={() => setChatOpen(!chatOpen)}
          style={{ cursor: 'pointer' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Bot size={20} className={chatOpen ? 'animate-pulse' : ''} />
            <span style={{ fontWeight: 700 }}>V-NEURON AI Assistant</span>
          </div>
          <span style={{ fontSize: '0.8rem' }}>{chatOpen ? '▼' : '▲'}</span>
        </div>
        
        {chatOpen && (
          <>
            <div className="chat-body" style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {messages.map((m, i) => (
                <div key={i} style={{ 
                  textAlign: m.sender === 'user' ? 'right' : 'left',
                  marginBottom: '0.5rem' 
                }}>
                  <div style={{ 
                    background: m.sender === 'user' ? '#e5e7eb' : '#eff6ff',
                    color: '#1f2937',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '12px',
                    display: 'inline-block',
                    maxWidth: '85%',
                    fontSize: '0.85rem',
                    lineHeight: '1.25rem',
                    textAlign: 'left',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
                  }}>
                    {m.text}
                  </div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>
            <form className="chat-input" onSubmit={handleSendMessage}>
              <input 
                type="text" 
                placeholder="Ask me to route you..." 
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
              />
              <button type="submit" style={{ display: 'flex', alignItems: 'center' }}>
                <Send size={18} />
              </button>
            </form>
          </>
        )}
      </div>

    </div>
  );
}

export default App;
