import { Paper, Typography, CircularProgress, Box, IconButton, Tooltip } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';

interface StatusCardProps {
  status: string;
  isRunning: boolean;
  onRefresh: () => void;
}

export function StatusCard({ status, isRunning, onRefresh }: StatusCardProps) {
  return (
    <Paper elevation={2} sx={{ flex: 1, p: 3, minWidth: 180, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <Box sx={{ position: 'relative', width: '100%', mb: 1 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, color: 'primary.main', textAlign: 'center' }}>Status</Typography>
        <Box sx={{ position: 'absolute', right: 0, top: '50%', transform: 'translateY(-50%)' }}>
          <Tooltip title="Refresh status">
            <span>
              <IconButton onClick={onRefresh} size="small" color="primary" disabled={status === 'loading'}>
                <RefreshIcon />
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </Box>
      <Typography
        variant="h3"
        sx={{
          color:
            status === 'stopped' ? 'error.main' :
            (status === 'loading' && !isRunning) ? 'orange' :
            isRunning ? 'success.main' :
            status === 'error' ? 'error.main' : 'text.primary',
          fontWeight: 700,
          textAlign: 'center',
          mb: 0.5,
          mt: 1
        }}
      >
        {status === 'loading' ? <CircularProgress size={32} sx={{ mr: 1, verticalAlign: 'middle' }} /> : null}
        {status === 'loading' && !isRunning ? 'Starting' : 
         status === 'running' ? 'Running' : 
         status === 'stopped' ? 'Stopped' : 
         status === 'error' ? 'Error' : 'Idle'}
      </Typography>
    </Paper>
  );
} 