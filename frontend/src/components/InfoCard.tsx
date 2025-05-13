import { Paper, Typography, Stack, Box } from '@mui/material';
import { useEffect, useState } from 'react';

interface InfoCardProps {
  stats: {
    urls_crawled: number;
    urls_failed: number;
    urls_in_queue: number;
  } | null;
  crawlMode: string;
  status: string;
}

export function InfoCard({ stats, crawlMode, status }: InfoCardProps) {
  const [displayStats, setDisplayStats] = useState(stats);
  const [displayMode, setDisplayMode] = useState(crawlMode);
  const [displayStatus, setDisplayStatus] = useState(status);

  useEffect(() => {
    setDisplayStats(stats);
    setDisplayMode(crawlMode);
    setDisplayStatus(status);
  }, [stats, crawlMode, status]);

  return (
    <Paper elevation={2} sx={{ flex: 1, p: 3, minWidth: 220, position: 'relative' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, color: 'primary.main', flexGrow: 1 }}>Info</Typography>
      </Box>
      {displayStats ? (
        <Stack spacing={0.5}>
          <Typography variant="body2">URLs Crawled: {displayStats.urls_crawled}</Typography>
          <Typography variant="body2">URLs Failed: {displayStats.urls_failed}</Typography>
          <Typography variant="body2">URLs in Queue: {displayStats.urls_in_queue}</Typography>
          <Typography variant="body2" sx={{ mt: 1, color: 'primary.main', fontWeight: 500 }}>
            Mode: {displayMode === 'fresh' ? 'Fresh Crawl' : displayMode === 'continue' ? 'Continue Crawl' : 'ReCrawl'}
          </Typography>
        </Stack>
      ) : (
        <Typography variant="body2" color="text.secondary">No data</Typography>
      )}
    </Paper>
  );
} 