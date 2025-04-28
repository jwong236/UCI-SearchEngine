import { 
  Typography, 
  Button, 
  Box, 
  Paper,
  Alert,
  Stack,
  CircularProgress,
  Collapse,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  TextField
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import RefreshIcon from '@mui/icons-material/Refresh';
import DeleteIcon from '@mui/icons-material/Delete';
import { useCrawlerForm } from '../hooks/useCrawlerForm';
import { useEffect, useRef, useState, useCallback } from 'react';

function useCrawlerLogs() {
  const [logs, setLogs] = useState<{ message: string; timestamp: string }[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/api/crawler/ws');
    wsRef.current = ws;
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLogs((prev) => [...prev.slice(-199), { message: data.message, timestamp: data.timestamp }]);
      } catch {}
    };
    ws.onerror = (e) => {
      // Optionally handle error
    };
    return () => ws.close();
  }, []);

  const clearLogs = useCallback(() => setLogs([]), []);
  return { logs, clearLogs };
}

export function Home() {
  const {
    SEED_URLS,
    status,
    message,
    isRunning,
    stats,
    failedUrls,
    failedLoading,
    handleStart,
    handleStop,
    handleShowFailedUrls,
    setFailedUrls,
    fetchStats,
    secretKey,
    setSecretKey
  } = useCrawlerForm();
  const { logs, clearLogs } = useCrawlerLogs();
  const [showFailed, setShowFailed] = useState(false);

  // Fetch failed URLs only when toggling on
  useEffect(() => {
    if (showFailed && !failedUrls) {
      handleShowFailedUrls();
    }
    if (!showFailed) {
      setFailedUrls(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showFailed]);

  return (
    <Box 
      sx={{ 
        width: '100%',
        display: 'flex', 
        flexDirection: 'column',
        alignItems: 'center',
        gap: 4
      }}
    >
      <Typography 
        variant="h3" 
        component="h1" 
        sx={{ 
          color: 'primary.main',
          mb: 3,
          textAlign: 'center',
          fontWeight: 500
        }}
      >
        Crawler
      </Typography>
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={3} sx={{ width: '100%', maxWidth: 900, mb: 2 }}>
        {/* Seed URLs Panel */}
        <Paper elevation={2} sx={{ flex: 1, p: 3, minWidth: 220 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Typography variant="h5" sx={{ fontWeight: 700, color: 'primary.main', mr: 1 }}>
              Seed URLs
            </Typography>
            <Tooltip title="Seed URLs are the initial starting points for the crawler. The crawler will begin crawling from these URLs and discover more links from there.">
              <HelpOutlineIcon color="action" fontSize="medium" sx={{ cursor: 'pointer' }} />
            </Tooltip>
          </Box>
          <Stack spacing={1}>
            {SEED_URLS.map((url, idx) => (
              <Typography key={idx} variant="body2" sx={{ wordBreak: 'break-all' }}>{url}</Typography>
            ))}
          </Stack>
        </Paper>
        {/* Status Panel */}
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
            {status === 'loading' && !isRunning ? 'Starting' : status === 'running' ? 'Running' : status === 'stopped' ? 'Stopped' : status === 'error' ? 'Error' : 'Idle'}
          </Typography>
        </Paper>
        {/* Statistics Panel */}
        <Paper elevation={2} sx={{ flex: 1, p: 3, minWidth: 220, position: 'relative' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Typography variant="h5" sx={{ fontWeight: 700, color: 'primary.main', flexGrow: 1 }}>Statistics</Typography>
            <Tooltip title="Refresh statistics">
              <span>
                <IconButton onClick={fetchStats} size="small" color="primary" disabled={status === 'loading'}>
                  <RefreshIcon />
                </IconButton>
              </span>
            </Tooltip>
          </Box>
          {stats ? (
            <Stack spacing={0.5}>
              <Typography variant="body2">URLs Crawled: {stats.urls_crawled}</Typography>
              <Typography variant="body2">URLs Failed: {stats.urls_failed}</Typography>
              <Typography variant="body2">Unique Domains: {stats.unique_domains}</Typography>
            </Stack>
          ) : (
            <Typography variant="body2" color="text.secondary">No data</Typography>
          )}
        </Paper>
      </Stack>
      {/* Real-Time Logs Panel */}
      <Paper elevation={2} sx={{ width: '100%', maxWidth: 900, p: 3, borderRadius: 2, mb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Typography variant="h5" sx={{ fontWeight: 700, color: 'primary.main', flexGrow: 1 }}>Real-Time Logs</Typography>
          <Tooltip title="Clear logs">
            <span>
              <IconButton onClick={clearLogs} size="small" color="primary">
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
                <span style={{ color: '#888', fontSize: '0.85em', marginRight: 8 }}>{new Date(log.timestamp).toLocaleTimeString()}</span>
                {log.message}
              </Typography>
            ))
          )}
        </Box>
      </Paper>
      {/* Actions Panel */}
      <Paper elevation={2} sx={{ width: '100%', maxWidth: 900, p: 3, borderRadius: 2, mt: 1 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, color: 'primary.main', mb: 2, textAlign: 'center' }}>Control Panel</Typography>
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
              {failedLoading ? <CircularProgress size={18} sx={{ mr: 1 }} /> : null}
              Show Failed URLs
            </Button>
            <Button 
              variant="contained"
              color="primary"
              onClick={handleStart}
              disabled={isRunning || status === 'loading' || !secretKey}
            >
              {status === 'loading' && !isRunning ? <CircularProgress size={18} sx={{ mr: 1, color: 'white' }} /> : null}
              Start Crawler
            </Button>
            <Button 
              variant="outlined"
              color="secondary"
              onClick={handleStop}
              disabled={!isRunning || status === 'loading' || !secretKey}
            >
              {status === 'loading' && isRunning ? <CircularProgress size={18} sx={{ mr: 1 }} /> : null}
              Stop Crawler
            </Button>
          </Stack>
          <Box sx={{ display: 'flex', justifyContent: 'center', width: '100%' }}>
            <TextField
              label="Secret Key"
              variant="outlined"
              value={secretKey}
              onChange={e => setSecretKey(e.target.value)}
              sx={{ maxWidth: 300 }}
              size="small"
              autoComplete="off"
            />
          </Box>
          {showFailed && failedUrls && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle1" color="text.secondary" gutterBottom>Failed URLs</Typography>
              <TableContainer component={Paper} sx={{ maxHeight: 240, overflow: 'auto', bgcolor: '#f9f9f9' }}>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>URL</TableCell>
                      <TableCell>Status Code</TableCell>
                      <TableCell>Last Crawled</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {failedUrls.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={3} align="center" sx={{ color: 'text.secondary' }}>
                          No failed URLs.
                        </TableCell>
                      </TableRow>
                    ) : (
                      failedUrls.map((row, idx) => (
                        <TableRow key={idx}>
                          <TableCell sx={{ wordBreak: 'break-all' }}>{row.url}</TableCell>
                          <TableCell>{row.status_code}</TableCell>
                          <TableCell>{row.last_crawled ? new Date(row.last_crawled).toLocaleString() : '-'}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </Stack>
      </Paper>
    </Box>
  );
} 