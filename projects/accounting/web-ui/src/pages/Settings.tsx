import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Stack,
  Alert,
  Divider,
  Switch,
  FormControlLabel,
} from '@mui/material';
import { useState } from 'react';

export default function Settings() {
  const [apiUrl, setApiUrl] = useState(import.meta.env.VITE_API_URL || 'http://localhost:8000/api');
  const [darkMode, setDarkMode] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    // In a real app, this would save to localStorage or user preferences
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Stack spacing={3}>
        {/* API Configuration */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              API Configuration
            </Typography>
            <Typography variant="body2" color="textSecondary" paragraph>
              Configure the backend API endpoint
            </Typography>
            <TextField
              label="API Base URL"
              fullWidth
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              helperText="The base URL for the accounting API (e.g., http://localhost:8000/api)"
            />
            <Box mt={2}>
              <Button variant="contained" onClick={handleSave}>
                Save API Settings
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* Appearance */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Appearance
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={darkMode}
                  onChange={(e) => setDarkMode(e.target.checked)}
                />
              }
              label="Dark Mode (Coming Soon)"
              disabled
            />
            <Typography variant="caption" color="textSecondary" display="block" mt={1}>
              Dark mode support will be added in a future update
            </Typography>
          </CardContent>
        </Card>

        {/* About */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              About
            </Typography>
            <Stack spacing={1}>
              <Box>
                <Typography variant="body2" color="textSecondary">
                  Application
                </Typography>
                <Typography variant="body1">
                  LiMOS Accounting Module - Web UI
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="textSecondary">
                  Version
                </Typography>
                <Typography variant="body1">
                  1.0.0
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="textSecondary">
                  API Status
                </Typography>
                <Typography variant="body1" color="success.main">
                  Connected
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>

        {saved && (
          <Alert severity="success">
            Settings saved successfully!
          </Alert>
        )}
      </Stack>
    </Box>
  );
}
