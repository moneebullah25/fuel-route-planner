import { useEffect } from "react";
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { Trip } from "../types";

// Fix default leaflet icon paths broken by Vite bundling
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

function makeIcon(color: string, label: string) {
  return L.divIcon({
    className: "",
    html: `
      <div style="
        background:${color};
        border:2px solid white;
        border-radius:50%;
        width:24px;height:24px;
        display:flex;align-items:center;justify-content:center;
        box-shadow:0 2px 6px rgba(0,0,0,0.4);
        font-size:10px;color:white;font-weight:bold;
      ">${label}</div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
}

function FitBounds({ coords }: { coords: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (coords.length > 1) {
      map.fitBounds(L.latLngBounds(coords), { padding: [40, 40] });
    }
  }, [map, coords]);
  return null;
}

interface Props {
  trip: Trip;
}

export default function TripMap({ trip }: Props) {
  // Backend returns [lon, lat]; Leaflet needs [lat, lon].
  const routeLatLng: [number, number][] = (trip.route_geometry ?? []).map(
    ([lon, lat]) => [lat, lon]
  );
  const start: [number, number] = [trip.start_coords[1], trip.start_coords[0]];
  const finish: [number, number] = [trip.finish_coords[1], trip.finish_coords[0]];
  const center = start ?? [37.0902, -95.7129];

  return (
    <MapContainer
      center={center}
      zoom={5}
      style={{ height: 520, width: "100%", borderRadius: 8 }}
      aria-label="Route map with fuel stops"
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      />

      {routeLatLng.length > 1 && (
        <Polyline positions={routeLatLng} color="#1d4ed8" weight={4} opacity={0.8} />
      )}

      <Marker position={start} icon={makeIcon("#64748b", "A")}>
        <Popup>
          <strong>Start</strong>
          <br />
          {trip.start_location}
        </Popup>
      </Marker>

      <Marker position={finish} icon={makeIcon("#3b82f6", "B")}>
        <Popup>
          <strong>Finish</strong>
          <br />
          {trip.finish_location}
        </Popup>
      </Marker>

      {trip.fuel_stops.map((stop) => (
        <Marker
          key={stop.order}
          position={[stop.coords[1], stop.coords[0]]}
          icon={makeIcon("#ef4444", String(stop.order + 1))}
        >
          <Popup>
            <strong>{stop.name}</strong>
            <br />
            <em>{stop.city}, {stop.state}</em>
            <br />
            <span style={{ fontSize: 12 }}>
              ${stop.price_per_gallon.toFixed(3)}/gal · {stop.gallons.toFixed(1)} gal · ${stop.cost.toFixed(2)}
            </span>
            <br />
            <span style={{ fontSize: 11, color: "#555" }}>Mile {stop.mile_marker.toFixed(0)}</span>
          </Popup>
        </Marker>
      ))}

      <FitBounds coords={[...routeLatLng, start, finish]} />
    </MapContainer>
  );
}
