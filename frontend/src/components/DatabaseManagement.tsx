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
import { Upload as UploadIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { useCrawlerForm } from '../hooks/useCrawlerForm';

interface DatabaseInfo {
  current: string;
  available: string[];
}

const DatabaseManagement: React.FC = () => {
  const [databases, setDatabases] = useState<DatabaseInfo>({ current: '', available: [] });
  const [selectedDb, setSelectedDb] = useState<string>('');
  const { secretKey } = useCrawlerForm();

  useEffect(() => {
    fetchDatabases();
  }, []);

  const fetchDatabases = async () => {
    try {
      const response = await fetch('/api/databases');
      const data = await response.json();
      setDatabases(data);
      setSelectedDb(data.current);
    } catch (error) {
      console.error('Failed to fetch databases:', error);
    }
  };

  const handleSwitchDatabase = async () => {
    if (!selectedDb || !secretKey) return;
    
    try {
      const response = await fetch(`/api/database/switch?db_name=${selectedDb}`, {
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
      const response = await fetch(`/api/database/delete?db_name=${selectedDb}`, {
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
      console.error('Failed to delete database:', error);
    }
  };

  const handleUploadDatabase = async (file: File) => {
    if (!secretKey) return;
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/crawler/upload-db', {
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
            onClick={handleSwitchDatabase}
            disabled={!selectedDb || selectedDb === databases.current || !secretKey}
          >
            Confirm
          </Button>
          
          <Button 
            variant="outlined"
            color="error"
            onClick={handleDeleteDatabase}
            disabled={!selectedDb || selectedDb === databases.current || !secretKey}
            startIcon={<DeleteIcon />}
          >
            Delete Database
          </Button>
          
          <Button 
            variant="outlined"
            component="label"
            startIcon={<UploadIcon />}
            disabled={!secretKey}
          >
            Upload Database
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
        </Stack>
      </Stack>
    </Card>
  );
};

export default DatabaseManagement; 