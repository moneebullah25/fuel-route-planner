export interface FuelStop {
  order: number;
  name: string;
  address: string;
  city: string;
  state: string;
  coords: [number, number]; // [lon, lat]
  mile_marker: number;
  price_per_gallon: number;
  gallons: number;
  cost: number;
}

export interface Trip {
  id: number;
  start_location: string;
  finish_location: string;
  start_coords: [number, number];  // [lon, lat]
  finish_coords: [number, number]; // [lon, lat]
  distance_miles: number;
  gallons_used: number;
  total_fuel_cost: number;
  route_geometry: [number, number][]; // [lon, lat]
  fuel_stops: FuelStop[];
  created_at: string;
}

export interface TripFormValues {
  start: string;
  finish: string;
}
