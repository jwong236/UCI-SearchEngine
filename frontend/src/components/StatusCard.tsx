import { Paper, Typography, CircularProgress } from '@mui/material';

interface StatusCardProps {
  status: string;
  isRunning: boolean;
}

export function StatusCard({ status, isRunning }: StatusCardProps) {
  return (
    <Paper elevation={2} sx={{ flex: 1, p: 3, minWidth: 180, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <Typography variant="h5" sx={{ fontWeight: 700, color: 'primary.main', mb: 1 }}>Status</Typography>
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