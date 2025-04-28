import { 
  Typography, 
  TextField, 
  Box, 
  Paper,
  InputAdornment
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import { useSearchForm } from '../hooks/useSearchForm';

export function Search() {
  const { query, setQuery, handleSearch } = useSearchForm();

  return (
    <Box 
      sx={{ 
        width: '100%',
        display: 'flex', 
        flexDirection: 'column',
        alignItems: 'center'
      }}
    >
      <Typography 
        variant="h3" 
        component="h1" 
        sx={{ 
          color: 'primary.main',
          mb: 6,
          textAlign: 'center',
          fontWeight: 500
        }}
      >
        UCI Search Engine
      </Typography>
      
      <Paper 
        component="form" 
        onSubmit={handleSearch}
        elevation={2}
        sx={{ 
          p: 3, 
          width: '100%',
          maxWidth: 600,
          borderRadius: 2
        }}
      >
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search UCI websites..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon color="action" />
              </InputAdornment>
            ),
            sx: {
              borderRadius: 2,
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: 'rgba(0, 0, 0, 0.1)',
              },
              '&:hover .MuiOutlinedInput-notchedOutline': {
                borderColor: 'rgba(0, 0, 0, 0.2)',
              },
            }
          }}
        />
      </Paper>
    </Box>
  );
} 