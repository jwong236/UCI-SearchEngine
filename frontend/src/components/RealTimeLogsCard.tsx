import { Paper, Typography, Box, IconButton, Tooltip } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';

interface Log {
  message: string;
  timestamp: string;
}

interface RealTimeLogsCardProps {
  logs: Log[];
  onClear: () => void;
}

export function RealTimeLogsCard({ logs, onClear }: RealTimeLogsCardProps) {
  return (
    <Paper elevation={2} sx={{ width: '100%', maxWidth: 900, p: 3, borderRadius: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, color: 'primary.main', flexGrow: 1 }}>Real-Time Logs</Typography>
        <Tooltip title="Clear logs">
          <span>
            <IconButton onClick={onClear} size="small" color="primary">
              <DeleteIcon />
            </IconButton>
          </span>
        </Tooltip>
      </Box>
      <Box sx={{ maxHeight: 200, overflow: 'auto', bgcolor: '#f9f9f9', p: 2, borderRadius: 1 }}>
        {logs.length === 0 ? (
          <Typography variant="body2" color="text.secondary">No logs yet.</Typography>
        ) : (
          logs.slice(-100).map((log, idx) => (
            <Typography key={idx} variant="body2" sx={{ fontFamily: 'monospace', mb: 0.5 }}>
              <span style={{ color: '#888', fontSize: '0.85em', marginRight: 8 }}>
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
              {log.message}
            </Typography>
          ))
        )}
      </Box>
    </Paper>
  );
} 