import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider, createTheme, CssBaseline, AppBar, Toolbar, Typography } from "@mui/material";
import LocalGasStationIcon from "@mui/icons-material/LocalGasStation";
import HomePage from "./pages/HomePage";
import ResultsPage from "./pages/ResultsPage";
import type { Trip } from "./types";

const queryClient = new QueryClient();

const theme = createTheme({
  palette: {
    primary: { main: "#1d4ed8" },
    secondary: { main: "#059669" },
    background: { default: "#f8fafc" },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  shape: { borderRadius: 8 },
});

export default function App() {
  const [trip, setTrip] = useState<Trip | null>(null);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AppBar position="static" elevation={0} sx={{ bgcolor: "primary.main" }}>
          <Toolbar>
            <LocalGasStationIcon sx={{ mr: 1 }} />
            <Typography variant="h6" sx={{ fontWeight: 700, flexGrow: 1 }}>
              Fuel Route Planner
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.8 }}>
              Cheapest fuel stops · 500-mi range · 10 MPG
            </Typography>
          </Toolbar>
        </AppBar>

        {trip ? (
          <ResultsPage trip={trip} onBack={() => setTrip(null)} />
        ) : (
          <HomePage onTripCreated={setTrip} />
        )}
      </ThemeProvider>
    </QueryClientProvider>
  );
}
