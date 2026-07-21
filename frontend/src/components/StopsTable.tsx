import {
  Box,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Paper,
} from "@mui/material";
import type { FuelStop } from "../types";

interface Props {
  stops: FuelStop[];
}

export default function StopsTable({ stops }: Props) {
  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
        Fuel Stops ({stops.length})
      </Typography>
      <Divider sx={{ mb: 2 }} />
      <TableContainer component={Paper} elevation={1} sx={{ overflowX: "auto" }}>
        <Table size="small" aria-label="Fuel stops table">
          <TableHead>
            <TableRow sx={{ bgcolor: "grey.100" }}>
              <TableCell>#</TableCell>
              <TableCell>Station</TableCell>
              <TableCell>City</TableCell>
              <TableCell align="right">Mile</TableCell>
              <TableCell align="right">$/gal</TableCell>
              <TableCell align="right">Gallons</TableCell>
              <TableCell align="right">Cost</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {stops.map((stop) => (
              <TableRow key={stop.order} hover>
                <TableCell>{stop.order + 1}</TableCell>
                <TableCell>{stop.name}</TableCell>
                <TableCell>{stop.city}, {stop.state}</TableCell>
                <TableCell align="right">{stop.mile_marker.toFixed(0)}</TableCell>
                <TableCell align="right">${stop.price_per_gallon.toFixed(3)}</TableCell>
                <TableCell align="right">{stop.gallons.toFixed(1)}</TableCell>
                <TableCell align="right">${stop.cost.toFixed(2)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
