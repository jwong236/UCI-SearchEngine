import { 
  Typography, 
  Paper,
  Box,
  Stack,
  Divider
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
        Statistics
      </Typography>
      
      <Box sx={{ width: '100%', maxWidth: 1200 }}>
        <Typography variant="h4" sx={{ mb: 3, color: 'primary.main' }}>
          Crawler Statistics
        </Typography>
        <Box sx={{ 
          display: 'flex', 
          flexWrap: 'wrap', 
          gap: 3,
          width: '100%',
          justifyContent: 'center',
          mb: 6
        }}>
          <Box sx={{ flex: '1 1 300px', maxWidth: 400 }}>
            <StatCard 
              title="URLs Crawled" 
              value={stats?.crawler_statistics?.urls_crawled || 0} 
            />
          </Box>
          <Box sx={{ flex: '1 1 300px', maxWidth: 400 }}>
            <StatCard 
              title="URLs Failed" 
              value={stats?.crawler_statistics?.urls_failed || 0} 
            />
          </Box>
          <Box sx={{ flex: '1 1 300px', maxWidth: 400 }}>
            <StatCard 
              title="Unique Domains" 
              value={stats?.crawler_statistics?.unique_domains || 0} 
            />
          </Box>
          <Box sx={{ flex: '1 1 300px', maxWidth: 400 }}>
            <StatCard 
              title="URLs in Queue" 
              value={stats?.crawler_statistics?.urls_in_queue || 0} 
            />
          </Box>
        </Box>

        <Divider sx={{ my: 6 }} />

        <Typography variant="h4" sx={{ mb: 3, color: 'primary.main' }}>
          Database Statistics
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
              title="Total Documents" 
              value={stats?.database_statistics?.total_documents || 0} 
            />
          </Box>
          <Box sx={{ flex: '1 1 300px', maxWidth: 400 }}>
            <StatCard 
              title="Total Terms" 
              value={stats?.database_statistics?.total_terms || 0} 
            />
          </Box>
          <Box sx={{ flex: '1 1 300px', maxWidth: 400 }}>
            <StatCard 
              title="Total Index Entries" 
              value={stats?.database_statistics?.total_index_entries || 0} 
            />
          </Box>
        </Box>
      </Box>
    </Box>
  );
} 