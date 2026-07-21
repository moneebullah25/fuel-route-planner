import { Box, Grid, Paper, Typography, Stack, Divider } from "@mui/material";
import RouteIcon from "@mui/icons-material/Route";
import LocalGasStationIcon from "@mui/icons-material/LocalGasStation";
import PaidIcon from "@mui/icons-material/Paid";
import OpacityIcon from "@mui/icons-material/Opacity";
import PriceCheckIcon from "@mui/icons-material/PriceCheck";
import type { Trip } from "../types";

interface CardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  color?: string;
}

function StatCard({ icon, label, value, color = "primary.main" }: CardProps) {
  return (
    <Paper elevation={2} sx={{ p: 2, height: "100%", borderTop: 3, borderColor: color }}>
      <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
        <Box sx={{ bgcolor: `${color}20`, borderRadius: 1, p: 1, color }}>{icon}</Box>
        <Box>
          <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
            {label}
          </Typography>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            {value}
          </Typography>
        </Box>
      </Stack>
    </Paper>
  );
}

interface Props {
  trip: Trip;
}

export default function SummaryCards({ trip }: Props) {
  const avgPrice = trip.gallons_used > 0 ? trip.total_fuel_cost / trip.gallons_used : 0;

  const cards: CardProps[] = [
    { icon: <RouteIcon />, label: "Total Distance", value: `${trip.distance_miles.toFixed(0)} mi`, color: "primary.main" },
    { icon: <PaidIcon />, label: "Total Fuel Cost", value: `$${trip.total_fuel_cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, color: "success.main" },
    { icon: <OpacityIcon />, label: "Fuel Used (10 MPG)", value: `${trip.gallons_used.toFixed(1)} gal`, color: "info.main" },
    { icon: <LocalGasStationIcon />, label: "Fuel Stops", value: `${trip.fuel_stops.length}`, color: "error.main" },
    { icon: <PriceCheckIcon />, label: "Avg Price / Gallon", value: `$${avgPrice.toFixed(3)}`, color: "secondary.main" },
  ];

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>Trip Summary</Typography>
      <Divider sx={{ mb: 2 }} />
      <Grid container spacing={2}>
        {cards.map((card) => (
          <Grid key={card.label} size={{ xs: 6, sm: 4, md: 2.4 }}>
            <StatCard {...card} />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
