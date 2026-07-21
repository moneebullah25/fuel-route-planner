import api from "./client";
import type { Trip, TripFormValues } from "../types";

export const createTrip = async (data: TripFormValues): Promise<Trip> => {
  const res = await api.post("/api/trips/", data);
  return res.data;
};

export const getTrip = async (id: number): Promise<Trip> => {
  const res = await api.get(`/api/trips/${id}/`);
  return res.data;
};
