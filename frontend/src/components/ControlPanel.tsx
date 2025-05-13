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
import { useState } from 'react';

interface ControlPanelProps {
  showSettings: boolean;
  setShowSettings: (show: boolean) => void;
  secretKey: string;
  status: string;
  isRunning: boolean;
  message: string;
  onStart: () => void;
  onStop: () => void;
  onShowFailedUrls: () => void;
  onClearMessage: () => void;
  failedLoading: boolean;
}

export function ControlPanel({ 
  showSettings, 
  setShowSettings, 
  secretKey,
  status,
  isRunning,
  message,
  onStart,
  onStop,
  onShowFailedUrls,
  onClearMessage,
  failedLoading
}: ControlPanelProps) {
  const [showFailed, setShowFailed] = useState(false);

  const handleShowFailed = () => {
    setShowFailed((prev) => !prev);
    if (!showFailed) {
      onShowFailedUrls();
    }
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
      
      <Collapse in={!!message}>
        {message && (
          <Alert 
            severity={status === 'error' ? 'error' : 'success'}
            action={
              <IconButton
                aria-label="close"
                color="inherit"
                size="small"
                onClick={onClearMessage}
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
          onClick={handleShowFailed}
          disabled={status === 'loading' || failedLoading}
          sx={showFailed ? { bgcolor: 'info.dark', color: 'white', '&:hover': { bgcolor: 'info.main' } } : {}}
        >
          Show Failed URLs
        </Button>
        <Button 
          variant="contained"
          color="primary"
          onClick={onStart}
          disabled={isRunning || status === 'loading' || !secretKey}
        >
          Start Crawler
        </Button>
        <Button 
          variant="outlined"
          color="error"
          onClick={onStop}
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
    </Paper>
  );
} 