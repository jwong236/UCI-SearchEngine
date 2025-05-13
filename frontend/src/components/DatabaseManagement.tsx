import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Button, 
  Select, 
  MenuItem, 
  Typography, 
  Stack,
  FormControl,
  InputLabel
} from '@mui/material';
import { Upload as UploadIcon, Delete as DeleteIcon, Download as DownloadIcon } from '@mui/icons-material';
import { useCrawlerForm } from '../hooks/useCrawlerForm';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

interface DatabaseInfo {
  current: string;
  available: string[];
}

interface DatabaseManagementProps {
  secretKey: string;
}

const DatabaseManagement: React.FC<DatabaseManagementProps> = ({ secretKey }) => {
  const [databases, setDatabases] = useState<DatabaseInfo>({ current: '', available: [] });
  const [selectedDb, setSelectedDb] = useState<string>('');

  useEffect(() => {
    fetchDatabases();
  }, []);

  const fetchDatabases = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/databases`);
      setDatabases(response.data);
      setSelectedDb(response.data.current);
    } catch (error) {
      console.error('Failed to fetch databases:', error);
    }
  };

  const handleChangeDatabase = async () => {
    if (!selectedDb || !secretKey) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/databases/switch?db_name=${selectedDb}`, {
        method: 'POST',
        headers: {
          'X-Secret-Key': secretKey
        }
      });
      const data = await response.json();
      
      if (data.status === 'success') {
        fetchDatabases();
      }
    } catch (error) {
      console.error('Failed to switch database:', error);
    }
  };

  const handleDeleteDatabase = async () => {
    if (!selectedDb || !secretKey) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/databases/${selectedDb}`, {
        method: 'DELETE',
        headers: {
          'X-Secret-Key': secretKey
        }
      });
      const data = await response.json();
      
      if (data.status === 'success') {
        fetchDatabases();
      }
    } catch (error) {
      console.error('Failed to delete database:', error);
    }
  };

  const handleDownloadDatabase = async () => {
    if (!selectedDb || !secretKey) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/databases/${selectedDb}/download`, {
        headers: {
          'X-Secret-Key': secretKey
        }
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${selectedDb}.sqlite`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Failed to download database:', error);
    }
  };

  const handleUploadDatabase = async (file: File) => {
    if (!secretKey) return;
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/databases/upload`, {
        method: 'POST',
        headers: {
          'X-Secret-Key': secretKey
        },
        body: formData,
      });
      const data = await response.json();
      
      if (data.status === 'success') {
        fetchDatabases();
      }
    } catch (error) {
      console.error('Failed to upload database:', error);
    }
  };

  return (
    <Card sx={{ 
      width: '100%', 
      maxWidth: 900, 
      p: 3, 
      borderRadius: 2 
    }}>
      <Typography variant="h5" sx={{ mb: 2, fontWeight: 700, color: 'primary.main' }}>
        Database Management
      </Typography>
      
      <Stack spacing={2}>
        <FormControl fullWidth>
          <InputLabel>Current Database</InputLabel>
          <Select
            value={selectedDb}
            onChange={(e) => setSelectedDb(e.target.value as string)}
            label="Current Database"
          >
            {databases.available.map(db => (
              <MenuItem key={db} value={db}>{db}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <Stack direction="row" spacing={2}>
          <Button 
            variant="contained"
            onClick={handleChangeDatabase}
            disabled={!selectedDb || selectedDb === databases.current || !secretKey}
          >
            Change
          </Button>
          
          <Button 
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleDownloadDatabase}
            disabled={!selectedDb || !secretKey}
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
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleUploadDatabase(file);
              }}
            />
          </Button>
          
          <Button 
            variant="outlined"
            color="error"
            onClick={handleDeleteDatabase}
            disabled={!selectedDb || selectedDb === databases.current || !secretKey}
            startIcon={<DeleteIcon />}
          >
            Delete
          </Button>
        </Stack>
      </Stack>
    </Card>
  );
};

export default DatabaseManagement; 