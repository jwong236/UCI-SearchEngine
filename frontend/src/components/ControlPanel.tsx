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

interface ControlPanelProps {
  showSettings: boolean;
  setShowSettings: (show: boolean) => void;
}

export function ControlPanel({ showSettings, setShowSettings }: ControlPanelProps) {
  const {
    status,
    message,
    isRunning,
    handleStart,
    handleStop,
    showFailed,
    setShowFailed,
    failedLoading,
    secretKey,
    setFailedUrls
  } = useCrawlerForm();

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
            onClick={() => setShowFailed((prev) => !prev)}
            disabled={status === 'loading' || failedLoading}
            sx={showFailed ? { bgcolor: 'info.dark', color: 'white', '&:hover': { bgcolor: 'info.main' } } : {}}
          >
            Show Failed URLs
          </Button>
          <Button 
            variant="contained"
            color="primary"
            onClick={handleStart}
            disabled={isRunning || status === 'loading' || !secretKey}
          >
            Start Crawler
          </Button>
          <Button 
            variant="outlined"
            color="secondary"
            onClick={handleStop}
            disabled={!isRunning || status === 'loading' || !secretKey}
          >
            Stop Crawler
          </Button>
        </Stack>
      </Stack>
    </Paper>
  );
} 