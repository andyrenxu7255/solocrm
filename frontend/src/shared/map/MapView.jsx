import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";

export function LeafletMap({ center = [39.9, 116.4], zoom = 12, markers = [], className = "" }) {
  return (
    <div className={`rounded-xl overflow-hidden border border-gray-200 ${className}`}>
      <MapContainer
        center={center}
        zoom={zoom}
        scrollWheelZoom={true}
        className="h-full w-full"
        style={{ minHeight: 400 }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {markers.map((m, i) => (
          <Marker key={i} position={[m.lat, m.lng]}>
            <Popup>{m.label}</Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
