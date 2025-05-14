import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Button, 
  Select, 
  MenuItem, 
  Typography, 
  Stack,
  FormControl,
  InputLabel,
  Alert,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Box
} from '@mui/material';
import { Upload as UploadIcon, Delete as DeleteIcon, Download as DownloadIcon } from '@mui/icons-material';
import axios from 'axios';

// Add File System Access API type declarations
interface FileSystemFileHandle {
  createWritable(): Promise<FileSystemWritableFileStream>;
}

interface FileSystemWritableFileStream extends WritableStream {
  write(data: any): Promise<void>;
  close(): Promise<void>;
}

interface ShowSaveFilePickerOptions {
  suggestedName?: string;
  types?: Array<{
    description: string;
    accept: Record<string, string[]>;
  }>;
}

declare global {
  interface Window {
    showSaveFilePicker(options?: ShowSaveFilePickerOptions): Promise<FileSystemFileHandle>;
  }
}

const API_BASE_URL = 'http://localhost:8000/api';

interface DatabaseInfo {
  current: string;
  available: string[];
}

interface DatabaseManagementProps {
  secretKey: string;
}

/**
 * Database management component for handling database operations
 */
const DatabaseManagement: React.FC<DatabaseManagementProps> = ({ secretKey }) => {
  const [databases, setDatabases] = useState<DatabaseInfo>({ current: '', available: [] });
  const [selectedDb, setSelectedDb] = useState<string>('');
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [downloadDialog, setDownloadDialog] = useState(false);
  const [downloadFilename, setDownloadFilename] = useState('');

  /**
   * Fetches available databases and sets the current one
   */
  const fetchDatabases = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/databases`);
      setDatabases(response.data);
      setSelectedDb(response.data.current || '');
    } catch (error) {
      console.error('Failed to fetch databases:', error);
      setMessage({ type: 'error', text: 'Failed to fetch databases' });
    }
  };

  useEffect(() => {
    fetchDatabases();
  }, []);

  const handleDatabaseChange = async () => {
    if (!selectedDb || !secretKey) return;
    
    try {
      await axios.post(`${API_BASE_URL}/databases/switch`, {
        db_name: selectedDb,
        secret_key: secretKey
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      setMessage({ type: 'success', text: 'Database switched successfully' });
      fetchDatabases();
    } catch (error: any) {
      console.error('Failed to switch database:', error);
      setMessage({ type: 'error', text: `Failed to switch database: ${error.response?.data?.detail || error.message}` });
    }
  };

  /**
   * Opens the download dialog with default filename (without extension)
   */
  const openDownloadDialog = () => {
    setDownloadFilename(selectedDb);
    setDownloadDialog(true);
  };

  /**
   * Downloads the database file with the specified filename while enforcing the .sqlite extension
   */
  const handleDownloadDatabase = async () => {
    if (!selectedDb || !secretKey) {
      setMessage({ type: 'error', text: 'No database selected or missing secret key' });
      return;
    }
    
    try {
      const response = await axios.get(`${API_BASE_URL}/databases/${selectedDb}/download`, {
        headers: {
          'X-Secret-Key': secretKey
        },
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], {
        type: 'application/octet-stream'
      });
      
      // Get base filename without extension
      let filename = downloadFilename.trim();
      
      // Remove any existing extension from user input
      filename = filename.replace(/\.[^/.]+$/, "");
      
      // If filename is empty, use the selectedDb name
      if (!filename) {
        filename = selectedDb;
      }
      
      if ('showSaveFilePicker' in window) {
        try {
          const fileHandle = await window.showSaveFilePicker({
            suggestedName: `${filename}.sqlite`,
            types: [{
              description: 'SQLite Database',
              accept: {'application/octet-stream': ['.sqlite']}
            }]
          });
          
          const writable = await fileHandle.createWritable();
          await writable.write(blob);
          await writable.close();
          
          setMessage({ type: 'success', text: 'Database downloaded successfully' });
        } catch (saveError) {
          console.error('Failed to save using File System Access API:', saveError);
          downloadUsingBlob(blob, `${filename}.sqlite`);
        }
      } else {
        downloadUsingBlob(blob, `${filename}.sqlite`);
      }
      
      setDownloadDialog(false);
    } catch (error) {
      console.error('Failed to download database:', error);
      
      if (axios.isAxiosError(error)) {
        setMessage({ 
          type: 'error', 
          text: `Download failed: ${error.response?.status || 'Unknown'} - ${error.message}` 
        });
      } else {
        setMessage({ type: 'error', text: `Download failed: ${error}` });
      }
      
      setDownloadDialog(false);
    }
  };

  /**
   * Downloads a blob using the traditional download method
   */
  const downloadUsingBlob = (blob: Blob, filename: string) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    link.setAttribute('target', '_blank');
    document.body.appendChild(link);
    link.click();
    
    setTimeout(() => {
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    }, 100);
  };

  const handleUploadDatabase = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !secretKey) return;
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      await axios.post(`${API_BASE_URL}/databases/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-Secret-Key': secretKey
        }
      });
      setMessage({ type: 'success', text: 'Database uploaded successfully' });
      await fetchDatabases();
    } catch (error) {
      console.error('Failed to upload database:', error);
      setMessage({ type: 'error', text: 'Failed to upload database' });
    }
  };

  const handleDeleteDatabase = async () => {
    if (!selectedDb || !secretKey) return;
    
    if (selectedDb === 'db-default') {
      setMessage({ type: 'error', text: 'Cannot delete the default database' });
      return;
    }
    
    try {
      await axios.delete(`${API_BASE_URL}/databases/${selectedDb}`, {
        headers: {
          'X-Secret-Key': secretKey
        }
      });
      setMessage({ type: 'success', text: 'Database deleted successfully' });
      await fetchDatabases();
    } catch (error) {
      console.error('Failed to delete database:', error);
      if (axios.isAxiosError(error)) {
        const errorMessage = error.response?.data?.detail || error.message;
        setMessage({ type: 'error', text: `Failed to delete database: ${errorMessage}` });
      } else {
        setMessage({ type: 'error', text: 'Failed to delete database' });
      }
    }
  };

  return (
    <Card elevation={2} sx={{ width: '100%', maxWidth: 900, p: 3, borderRadius: 2 }}>
      <Typography variant="h5" sx={{ fontWeight: 700, color: 'primary.main', mb: 2 }}>
        Database Management
      </Typography>
      
      <Box sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
        <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>
          Current database:
        </Typography>
        <Typography variant="body1" fontWeight="medium">
          {databases.current || 'None'}
        </Typography>
      </Box>
      
      <Stack spacing={2}>
        <FormControl fullWidth>
          <InputLabel id="database-select-label">Select Database</InputLabel>
          <Select
            labelId="database-select-label"
            value={selectedDb}
            label="Select Database"
            onChange={(e) => setSelectedDb(e.target.value)}
          >
            {databases.available.map((db) => (
              <MenuItem key={db} value={db}>
                {db}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <Stack direction="row" spacing={2} justifyContent="center">
          <Button
            variant="contained"
            onClick={handleDatabaseChange}
            disabled={!selectedDb || selectedDb === databases.current}
          >
            Change
          </Button>
          
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={openDownloadDialog}
            disabled={!selectedDb}
          >
            Download
          </Button>
          
          <Button
            variant="outlined"
            component="label"
            startIcon={<UploadIcon />}
            disabled={!secretKey}
          >
            Upload
            <input
              type="file"
              hidden
              accept=".sqlite"
              onChange={handleUploadDatabase}
            />
          </Button>
          
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={handleDeleteDatabase}
            disabled={!selectedDb || selectedDb === 'db-default'}
          >
            Delete
          </Button>
        </Stack>
      </Stack>

      <Dialog 
        open={downloadDialog} 
        onClose={() => setDownloadDialog(false)}
        aria-labelledby="download-dialog-title"
        container={() => document.getElementById('root') || document.body}
      >
        <DialogTitle id="download-dialog-title">Download Database</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Filename (without extension)"
            type="text"
            fullWidth
            value={downloadFilename}
            onChange={(e) => setDownloadFilename(e.target.value)}
            helperText="Enter a name for the downloaded file. The .sqlite extension will be added automatically."
            slotProps={{
              input: {
                endAdornment: <Typography color="text.secondary">.sqlite</Typography>
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDownloadDialog(false)}>Cancel</Button>
          <Button onClick={handleDownloadDatabase} variant="contained">Download</Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={!!message}
        autoHideDuration={6000}
        onClose={() => setMessage(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={() => setMessage(null)} 
          severity={message?.type} 
          sx={{ width: '100%' }}
        >
          {message?.text}
        </Alert>
      </Snackbar>
    </Card>
  );
};

export default DatabaseManagement; 