import {
  Box,
  Button,
  Container,
  Divider,
  Stack,
  Typography,
  Chip,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";

import TripMap from "../components/TripMap";
import SummaryCards from "../components/SummaryCards";
import StopsTable from "../components/StopsTable";
import type { Trip } from "../types";

interface Props {
  trip: Trip;
  onBack: () => void;
}

export default function ResultsPage({ trip, onBack }: Props) {
  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={2}
        sx={{ justifyContent: "space-between", alignItems: { sm: "center" }, mb: 3 }}
      >
        <Box>
          <Button startIcon={<ArrowBackIcon />} onClick={onBack} sx={{ mb: 1 }}>
            New Route
          </Button>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            {trip.start_location} → {trip.finish_location}
          </Typography>
          <Stack direction="row" spacing={1} sx={{ mt: 0.5, flexWrap: "wrap" }}>
            <Chip label={`${trip.distance_miles.toFixed(0)} miles`} size="small" color="primary" />
            <Chip label={`$${trip.total_fuel_cost.toFixed(2)} fuel`} size="small" color="success" />
            <Chip label={`${trip.fuel_stops.length} stops`} size="small" color="error" variant="outlined" />
          </Stack>
        </Box>
      </Stack>

      <SummaryCards trip={trip} />

      <Divider sx={{ my: 3 }} />

      <TripMap trip={trip} />

      <StopsTable stops={trip.fuel_stops} />
    </Container>
  );
}
