import { 
  Typography, 
  Paper,
  Box,
  Stack
} from '@mui/material';
import { useCrawlerStats } from '../hooks/useCrawlerStats';

export function Statistics() {
  const { stats } = useCrawlerStats();

  const StatCard = ({ title, value }: { title: string; value: number | string }) => (
    <Paper sx={{ p: 3, textAlign: 'center' }}>
      <Typography variant="h6" color="primary" gutterBottom>
        {title}
      </Typography>
      <Typography variant="h4">
        {value}
      </Typography>
    </Paper>
  );

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
        Crawler Statistics
      </Typography>
      
      <Box sx={{ 
        display: 'flex', 
        flexWrap: 'wrap', 
        gap: 3,
        width: '100%',
        justifyContent: 'center'
      }}>
        <Box sx={{ flex: '1 1 300px', maxWidth: 400 }}>
          <StatCard 
            title="URLs Crawled" 
            value={stats?.urls_crawled || 0} 
          />
        </Box>
        <Box sx={{ flex: '1 1 300px', maxWidth: 400 }}>
          <StatCard 
            title="URLs Failed" 
            value={stats?.urls_failed || 0} 
          />
        </Box>
        <Box sx={{ flex: '1 1 300px', maxWidth: 400 }}>
          <StatCard 
            title="Unique Domains" 
            value={stats?.unique_domains || 0} 
          />
        </Box>
      </Box>
    </Box>
  );
} 