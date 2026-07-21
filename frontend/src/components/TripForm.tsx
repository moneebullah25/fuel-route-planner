import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Box,
  Button,
  CircularProgress,
  Stack,
  TextField,
  Typography,
  Paper,
  Alert,
} from "@mui/material";
import LocalGasStationIcon from "@mui/icons-material/LocalGasStation";
import type { TripFormValues } from "../types";

const schema = z.object({
  start: z.string().min(3, "Enter a start location"),
  finish: z.string().min(3, "Enter a finish location"),
});

interface Props {
  onSubmit: (values: TripFormValues) => void;
  loading: boolean;
  error?: string;
}

export default function TripForm({ onSubmit, loading, error }: Props) {
  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<TripFormValues>({
    resolver: zodResolver(schema),
    defaultValues: { start: "", finish: "" },
  });

  return (
    <Paper elevation={3} sx={{ p: 4, maxWidth: 600, mx: "auto", mt: 4 }}>
      <Stack direction="row" spacing={1} sx={{ alignItems: "center", mb: 3 }}>
        <LocalGasStationIcon color="primary" fontSize="large" />
        <Typography variant="h5" sx={{ fontWeight: 700 }}>
          Plan a Route
        </Typography>
      </Stack>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box component="form" onSubmit={handleSubmit(onSubmit)}>
        <Stack spacing={3}>
          <Controller
            name="start"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Start Location"
                placeholder="e.g. Dallas, TX"
                error={!!errors.start}
                helperText={errors.start?.message}
                fullWidth
                slotProps={{ htmlInput: { "aria-label": "Start location" } }}
              />
            )}
          />

          <Controller
            name="finish"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Finish Location"
                placeholder="e.g. Chicago, IL"
                error={!!errors.finish}
                helperText={errors.finish?.message}
                fullWidth
                slotProps={{ htmlInput: { "aria-label": "Finish location" } }}
              />
            )}
          />

          <Button
            type="submit"
            variant="contained"
            size="large"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={18} color="inherit" /> : null}
            aria-label="Plan route"
          >
            {loading ? "Planning Route..." : "Plan Route & Find Fuel"}
          </Button>
        </Stack>
      </Box>
    </Paper>
  );
}
