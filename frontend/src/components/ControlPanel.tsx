import { 
  Paper, 
  Box, 
  Typography, 
  Button, 
  Stack, 
  IconButton,
  Tooltip,
  Collapse,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  TablePagination
} from '@mui/material';
import { 
  Settings as SettingsIcon, 
  Close as CloseIcon,
  KeyboardArrowDown as ExpandMoreIcon,
  KeyboardArrowUp as ExpandLessIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { useState, useEffect } from 'react';

interface FailedUrl {
  url: string;
  error: string;
  failed_at: string | null;
}

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
  failedUrls: FailedUrl[] | null;
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
  failedLoading,
  failedUrls
}: ControlPanelProps) {
  const [showFailed, setShowFailed] = useState(false);
  const [expandedRows, setExpandedRows] = useState<number[]>([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [isDataStale, setIsDataStale] = useState(false);

  useEffect(() => {
    if (showFailed && (!failedUrls || isDataStale)) {
      onShowFailedUrls();
      setIsDataStale(false);
    }
  }, [showFailed, failedUrls, onShowFailedUrls, isDataStale]);

  const handleShowFailed = () => {
    setShowFailed(prev => !prev);
    setPage(0);
    setIsDataStale(true);
  };

  const toggleRowExpansion = (index: number) => {
    setExpandedRows(prev => 
      prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]
    );
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
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
      
      <Collapse in={!!message} sx={{ mb: 3 }}>
        {message && (
          <Alert 
            severity={status === 'error' ? 'error' : 'success'}
            onClose={onClearMessage}
            sx={{ 
              borderRadius: 1,
              '& .MuiAlert-action': {
                alignItems: 'center',
                padding: '4px 0 4px 8px',
                '& .MuiIconButton-root': {
                  padding: '4px',
                  '&:hover': {
                    backgroundColor: 'rgba(0, 0, 0, 0.04)'
                  }
                }
              },
              '& .MuiAlert-icon': {
                padding: '8px 0 8px 16px'
              },
              '& .MuiAlert-message': {
                padding: '8px 0'
              }
            }}
          >
            {message}
          </Alert>
        )}
      </Collapse>
      
      <Stack direction="row" spacing={2}>
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

      <Collapse in={showFailed} sx={{ mt: 2 }}>
        <Paper elevation={0} sx={{ bgcolor: 'background.default', p: 2, borderRadius: 1 }}>
          {failedLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <CircularProgress size={24} />
            </Box>
          ) : failedUrls && failedUrls.length > 0 ? (
            <>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1 }}>
                <Button 
                  size="small" 
                  onClick={() => { setIsDataStale(true); }} 
                  startIcon={<RefreshIcon />} 
                  disabled={failedLoading}
                >
                  Refresh
                </Button>
              </Box>
              <TableContainer sx={{ width: '100%' }}>
                <Table size="small" sx={{ tableLayout: 'fixed' }}>
                  <TableHead>
                    <TableRow>
                      <TableCell width="25%">URL</TableCell>
                      <TableCell width="35%">Error</TableCell>
                      <TableCell width="15%">Failed At</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {failedUrls
                      .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                      .map((url, idx) => (
                        <TableRow key={idx}>
                          <TableCell width="25%" sx={{ maxWidth: '25%' }}>
                            <Typography sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {url.url}
                            </Typography>
                            <Collapse in={expandedRows.includes(idx)} timeout="auto" unmountOnExit>
                              <Box sx={{ mt: 1, maxWidth: '100%' }}>
                                <Typography variant="body2" fontWeight="medium" sx={{ mb: 0.5 }}>
                                  Full URL:
                                </Typography>
                                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', backgroundColor: 'rgba(0,0,0,0.04)', p: 1, borderRadius: 1, fontSize: '0.75rem' }}>
                                  {url.url}
                                </Typography>
                              </Box>
                            </Collapse>
                          </TableCell>
                          
                          <TableCell width="35%" sx={{ maxWidth: '35%' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <Typography variant="body2" sx={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {url.error}
                              </Typography>
                              <IconButton size="small" onClick={() => toggleRowExpansion(idx)} sx={{ ml: 0.5, p: 0.5, flexShrink: 0 }}>
                                {expandedRows.includes(idx) ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
                              </IconButton>
                            </Box>
                            <Collapse in={expandedRows.includes(idx)} timeout="auto" unmountOnExit>
                              <Box sx={{ mt: 1, maxWidth: '100%' }}>
                                <Typography variant="body2" fontWeight="medium" sx={{ mb: 0.5 }}>
                                  Full Error:
                                </Typography>
                                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', backgroundColor: 'rgba(0,0,0,0.04)', p: 1, borderRadius: 1, fontSize: '0.75rem' }}>
                                  {url.error}
                                </Typography>
                              </Box>
                            </Collapse>
                          </TableCell>
                          
                          <TableCell width="15%" sx={{ maxWidth: '15%', whiteSpace: 'nowrap' }}>
                            {url.failed_at ? new Date(url.failed_at).toLocaleString() : 'N/A'}
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
                <TablePagination
                  component="div"
                  count={failedUrls.length}
                  rowsPerPage={rowsPerPage}
                  page={page}
                  onPageChange={(e, newPage) => setPage(newPage)}
                  onRowsPerPageChange={(e) => {
                    setRowsPerPage(parseInt(e.target.value, 10));
                    setPage(0);
                  }}
                  rowsPerPageOptions={[10, 25, 50, 100]}
                />
              </TableContainer>
            </>
          ) : (
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
              No failed URLs to display
            </Typography>
          )}
        </Paper>
      </Collapse>
    </Paper>
  );
} 