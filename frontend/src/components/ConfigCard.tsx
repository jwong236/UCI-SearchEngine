import { Paper, Typography, Stack, Box, Tooltip, TextField, Button, Dialog, DialogTitle, DialogContent, DialogActions, IconButton } from '@mui/material';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import DeleteIcon from '@mui/icons-material/Delete';
import { useState } from 'react';

interface ConfigCardProps {
  seedUrls: string[];
  secretKey: string;
  onSecretKeyChange: (key: string) => void;
  onSeedUrlsChange: (urls: string[]) => void;
}

export function ConfigCard({ seedUrls, secretKey, onSecretKeyChange, onSeedUrlsChange }: ConfigCardProps) {
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editingUrls, setEditingUrls] = useState<string[]>(seedUrls);

  const handleSave = () => {
    onSeedUrlsChange(editingUrls);
    setShowEditDialog(false);
  };

  const handleCancel = () => {
    setEditingUrls(seedUrls);
    setShowEditDialog(false);
  };

  const handleDeleteUrl = (index: number) => {
    if (editingUrls.length > 1) {
      const newUrls = [...editingUrls];
      newUrls.splice(index, 1);
      setEditingUrls(newUrls);
    }
  };

  return (
    <Paper elevation={2} sx={{ flex: 1, p: 3, minWidth: 220 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, color: 'primary.main', mr: 1 }}>
          Config
        </Typography>
      </Box>
      
      <Stack spacing={2}>
        <TextField
          label="Secret Key"
          variant="outlined"
          value={secretKey}
          onChange={(e) => onSecretKeyChange(e.target.value)}
          fullWidth
          size="small"
          type="password"
        />
        
        <Button 
          variant="outlined" 
          onClick={() => setShowEditDialog(true)}
          disabled={!secretKey}
        >
          Edit Seed URLs
        </Button>
      </Stack>

      <Dialog open={showEditDialog} onClose={handleCancel} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography variant="h6" sx={{ flexGrow: 1 }}>Edit Seed URLs</Typography>
            <Tooltip title="Seed URLs are the initial starting points for the crawler. The crawler will begin crawling from these URLs and discover more links from there.">
              <HelpOutlineIcon color="action" fontSize="medium" sx={{ cursor: 'pointer' }} />
            </Tooltip>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 2 }}>
            {editingUrls.map((url, idx) => (
              <Box key={idx} sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  label={`Seed URL ${idx + 1}`}
                  variant="outlined"
                  value={url}
                  onChange={(e) => {
                    const newUrls = [...editingUrls];
                    newUrls[idx] = e.target.value;
                    setEditingUrls(newUrls);
                  }}
                  fullWidth
                />
                <IconButton 
                  onClick={() => handleDeleteUrl(idx)}
                  disabled={editingUrls.length <= 1}
                  color="error"
                >
                  <DeleteIcon />
                </IconButton>
              </Box>
            ))}
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button 
                variant="outlined" 
                onClick={() => setEditingUrls([...editingUrls, ''])}
                fullWidth
                sx={{ 
                  height: '56px',
                  backgroundColor: 'white',
                  '&:hover': {
                    backgroundColor: 'white',
                    borderColor: 'primary.main',
                    borderWidth: '2px'
                  }
                }}
              >
                Add URL
              </Button>
              <Box sx={{ width: '40px' }} /> {/* Spacer to match the delete button width */}
            </Box>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancel}>Cancel</Button>
          <Button onClick={handleSave} variant="contained" sx={{ minWidth: '120px' }}>Save</Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
} 