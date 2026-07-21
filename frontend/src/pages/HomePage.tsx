import { useState } from "react";
import { Container, Box, Typography, LinearProgress } from "@mui/material";
import TripForm from "../components/TripForm";
import { createTrip } from "../api/trips";
import type { Trip, TripFormValues } from "../types";

interface Props {
  onTripCreated: (trip: Trip) => void;
}

export default function HomePage({ onTripCreated }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();

  const handleSubmit = async (values: TripFormValues) => {
    setLoading(true);
    setError(undefined);
    try {
      const trip = await createTrip(values);
      onTripCreated(trip);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ||
        "Something went wrong. Check your locations and try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ py: 6, textAlign: "center" }}>
        <Typography variant="h3" gutterBottom sx={{ fontWeight: 800 }}>
          Fuel Route Planner
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 4 }}>
          Find the most cost-effective fuel stops along any US driving route
        </Typography>
      </Box>

      <TripForm onSubmit={handleSubmit} loading={loading} error={error} />

      {loading && (
        <Box sx={{ mt: 4, maxWidth: 600, mx: "auto" }}>
          <LinearProgress sx={{ borderRadius: 1 }} />
          <Typography variant="caption" color="text.secondary" sx={{ display: "block", textAlign: "center", mt: 1 }}>
            Geocoding locations, routing, and optimizing fuel stops…
          </Typography>
        </Box>
      )}
    </Container>
  );
}
