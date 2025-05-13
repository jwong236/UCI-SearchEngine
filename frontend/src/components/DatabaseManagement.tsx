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
  Snackbar
} from '@mui/material';
import { Upload as UploadIcon, Delete as DeleteIcon, Download as DownloadIcon } from '@mui/icons-material';
import axios from 'axios';

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
      });
      setMessage({ type: 'success', text: 'Database switched successfully' });
      fetchDatabases();
    } catch (error) {
      console.error('Failed to switch database:', error);
      setMessage({ type: 'error', text: 'Failed to switch database' });
    }
  };

  const handleDownloadDatabase = async () => {
    if (!selectedDb || !secretKey) return;
    
    try {
      const response = await axios.get(`${API_BASE_URL}/databases/${selectedDb}/download`, {
        headers: {
          'X-Secret-Key': secretKey
        },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${selectedDb}.sqlite`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setMessage({ type: 'success', text: 'Database downloaded successfully' });
    } catch (error) {
      console.error('Failed to download database:', error);
      setMessage({ type: 'error', text: 'Failed to download database' });
    }
  };

  const handleUploadDatabase = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !secretKey) return;
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('secret_key', secretKey);

    try {
      await axios.post(`${API_BASE_URL}/databases/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-Secret-Key': secretKey
        }
      });
      setMessage({ type: 'success', text: 'Database uploaded successfully' });
      fetchDatabases();
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
      fetchDatabases();
    } catch (error) {
      console.error('Failed to delete database:', error);
      setMessage({ type: 'error', text: 'Failed to delete database' });
    }
  };

  return (
    <Card elevation={2} sx={{ width: '100%', maxWidth: 900, p: 3, borderRadius: 2 }}>
      <Typography variant="h5" sx={{ fontWeight: 700, color: 'primary.main', mb: 2 }}>
        Database Management
      </Typography>
      
      <Stack spacing={2}>
        <FormControl fullWidth>
          <InputLabel id="database-select-label">Current Database</InputLabel>
          <Select
            labelId="database-select-label"
            value={selectedDb}
            label="Current Database"
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
            onClick={handleDownloadDatabase}
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