import { 
  Typography, 
  Box, 
  Paper,
  Stack,
  CircularProgress,
  IconButton,
  Tooltip,
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
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import RefreshIcon from '@mui/icons-material/Refresh';
import DeleteIcon from '@mui/icons-material/Delete';
import { useCrawlerForm, CrawlMode } from '../hooks/useCrawlerForm';
import { useEffect, useState } from 'react';
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
    setSecretKey,
    crawlMode,
    setCrawlMode
  } = useCrawlerForm();
  const { logs, clearLogs } = useCrawlerLogs();
  const [showFailed, setShowFailed] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    if (showFailed && !failedUrls) {
      handleShowFailedUrls();
    }
    if (!showFailed) {
      setFailedUrls(null);
    }
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
        <ConfigCard 
          seedUrls={SEED_URLS}
          secretKey={secretKey}
          onSecretKeyChange={setSecretKey}
          onSeedUrlsChange={(urls) => {
            // TODO: Implement seed URL update in the backend
            console.log('New seed URLs:', urls);
          }}
        />
        <StatusCard status={status} isRunning={isRunning} />
        <InfoCard 
          stats={stats || null} 
          crawlMode={crawlMode} 
          onRefresh={fetchStats}
          status={status} 
        />
      </Stack>

      <ControlPanel showSettings={showSettings} setShowSettings={setShowSettings} secretKey={secretKey} />
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
          {failedUrls && failedUrls.length > 0 ? (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>URL</TableCell>
                    <TableCell>Error</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {failedUrls.map((url, index) => (
                    <TableRow key={index}>
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