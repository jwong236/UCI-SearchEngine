import { 
  Paper, 
  Box, 
  Typography, 
  Button, 
  Stack, 
  IconButton,
  Tooltip,
  Collapse,
  Alert
} from '@mui/material';
import { Settings as SettingsIcon, Close as CloseIcon } from '@mui/icons-material';
import { useCrawlerForm } from '../hooks/useCrawlerForm';
import { useState } from 'react';

interface ControlPanelProps {
  showSettings: boolean;
  setShowSettings: (show: boolean) => void;
  secretKey: string;
}

export function ControlPanel({ showSettings, setShowSettings, secretKey }: ControlPanelProps) {
  const [showFailed, setShowFailed] = useState(false);
  const {
    status,
    message,
    isRunning,
    handleStart,
    handleStop,
    failedLoading,
    setFailedUrls
  } = useCrawlerForm({ secretKey });

  const handleStartWithKey = () => {
    handleStart();
  };

  const handleStopWithKey = () => {
    handleStop();
  };

  return (
    <Paper elevation={2} sx={{ width: '100%', maxWidth: 900, p: 3, borderRadius: 2, mt: 1 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, color: 'primary.main' }}>Control Panel</Typography>
        <Tooltip title="Settings">
          <IconButton onClick={() => setShowSettings(true)} color="primary">
            <SettingsIcon />
          </IconButton>
        </Tooltip>
      </Box>
      <Stack spacing={2}>
        <Collapse in={!!message}>
          {message && (
            <Alert 
              severity={status === 'error' ? 'error' : 'success'}
              action={
                <IconButton
                  aria-label="close"
                  color="inherit"
                  size="small"
                  onClick={() => setFailedUrls(null)}
                >
                  <CloseIcon fontSize="inherit" />
                </IconButton>
              }
              sx={{ borderRadius: 1 }}
            >
              {message}
            </Alert>
          )}
        </Collapse>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} justifyContent="center" alignItems="center">
          <Button 
            variant={showFailed ? 'contained' : 'outlined'}
            color={showFailed ? 'info' : 'info'}
            onClick={() => setShowFailed((prev: boolean) => !prev)}
            disabled={status === 'loading' || failedLoading}
            sx={showFailed ? { bgcolor: 'info.dark', color: 'white', '&:hover': { bgcolor: 'info.main' } } : {}}
          >
            Show Failed URLs
          </Button>
          <Button 
            variant="contained"
            color="primary"
            onClick={handleStartWithKey}
            disabled={isRunning || status === 'loading' || !secretKey}
          >
            Start Crawler
          </Button>
          <Button 
            variant="outlined"
            color="error"
            onClick={handleStopWithKey}
            disabled={!isRunning || status === 'loading' || !secretKey}
            sx={{ 
              borderColor: 'error.main',
              color: 'error.main',
              '&:hover': {
                backgroundColor: 'error.main',
                color: 'white',
                borderColor: 'error.main'
              }
            }}
          >
            Stop Crawler
          </Button>
        </Stack>
      </Stack>
    </Paper>
  );
} 