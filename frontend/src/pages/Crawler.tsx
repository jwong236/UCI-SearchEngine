import { 
  Typography, 
  Box, 
  Stack,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  FormLabel,
  Radio,
  RadioGroup,
  FormControlLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import { useCrawlerForm, CrawlMode } from '../hooks/useCrawlerForm';
import { useEffect, useState, useCallback } from 'react';
import { ControlPanel } from '../components/ControlPanel';
import DatabaseManagement from '../components/DatabaseManagement';
import { ConfigCard } from '../components/ConfigCard';
import { StatusCard } from '../components/StatusCard';
import { InfoCard } from '../components/InfoCard';
import { RealTimeLogsCard } from '../components/RealTimeLogsCard';

function useCrawlerLogs() {
  const [logs, setLogs] = useState<{ message: string; timestamp: string }[]>([]);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/api/crawler/ws');
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLogs((prev) => [...prev.slice(-199), { message: data.message, timestamp: data.timestamp }]);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    return () => ws.close();
  }, []);

  const clearLogs = () => setLogs([]);
  return { logs, clearLogs };
}

export function Crawler() {
  const [secretKey, setSecretKey] = useState('');
  const {
    SEED_URLS,
    currentSeedUrls,
    setCurrentSeedUrls,
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
    refreshStats,
    crawlMode,
    setCrawlMode
  } = useCrawlerForm({ secretKey });

  const { logs, clearLogs } = useCrawlerLogs();
  const [showFailed, setShowFailed] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const handleRefresh = useCallback(async () => {
    await refreshStats();
  }, [refreshStats]);

  const handleClearMessage = useCallback(() => {
    setFailedUrls(null);
  }, [setFailedUrls]);

  useEffect(() => {
    if (showFailed && !failedUrls) {
      handleShowFailedUrls();
    }
    if (!showFailed) {
      setFailedUrls(null);
    }
  }, [showFailed, failedUrls, handleShowFailedUrls, setFailedUrls]);

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
        <ConfigCard 
          seedUrls={currentSeedUrls}
          secretKey={secretKey}
          onSecretKeyChange={setSecretKey}
          onSeedUrlsChange={setCurrentSeedUrls}
        />
        <StatusCard status={status} isRunning={isRunning} onRefresh={handleRefresh} />
        <InfoCard 
          stats={stats || null} 
          crawlMode={crawlMode} 
          status={status} 
        />
      </Stack>

      <ControlPanel 
        showSettings={showSettings} 
        setShowSettings={setShowSettings} 
        secretKey={secretKey}
        status={status}
        isRunning={isRunning}
        message={message}
        onStart={handleStart}
        onStop={handleStop}
        onShowFailedUrls={handleShowFailedUrls}
        onClearMessage={handleClearMessage}
        failedLoading={failedLoading}
      />
      <DatabaseManagement secretKey={secretKey} />
      <RealTimeLogsCard logs={logs} onClear={clearLogs} />

      {/* Settings Dialog */}
      <Dialog open={showSettings} onClose={() => setShowSettings(false)}>
        <DialogTitle>Crawler Settings</DialogTitle>
        <DialogContent>
          <FormControl component="fieldset" sx={{ mt: 2 }}>
            <FormLabel component="legend">Crawl Mode</FormLabel>
            <RadioGroup
              value={crawlMode}
              onChange={(e) => setCrawlMode(e.target.value as CrawlMode)}
            >
              <FormControlLabel 
                value="fresh" 
                control={<Radio />} 
                label="Fresh Crawl (Clear database and start from scratch)" 
              />
              <FormControlLabel 
                value="continue" 
                control={<Radio />} 
                label="Continue Crawl (Continue from where we left off)" 
              />
              <FormControlLabel 
                value="recrawl" 
                control={<Radio />} 
                label="ReCrawl (Start from beginning but keep database)" 
              />
            </RadioGroup>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSettings(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Failed URLs Dialog */}
      <Dialog 
        open={showFailed} 
        onClose={() => setShowFailed(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Failed URLs</DialogTitle>
        <DialogContent>
          {failedLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : failedUrls && failedUrls.length > 0 ? (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>URL</TableCell>
                    <TableCell>Error</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {failedUrls.map((url, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{url.url}</TableCell>
                      <TableCell>{url.error}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Typography>No failed URLs to display.</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowFailed(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
} 