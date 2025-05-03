import { Paper, Typography, Stack, Box, Tooltip } from '@mui/material';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';

interface SeedUrlsCardProps {
  seedUrls: string[];
}

export function SeedUrlsCard({ seedUrls }: SeedUrlsCardProps) {
  return (
    <Paper elevation={2} sx={{ flex: 1, p: 3, minWidth: 220 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, color: 'primary.main', mr: 1 }}>
          Seed URLs
        </Typography>
        <Tooltip title="Seed URLs are the initial starting points for the crawler. The crawler will begin crawling from these URLs and discover more links from there.">
          <HelpOutlineIcon color="action" fontSize="medium" sx={{ cursor: 'pointer' }} />
        </Tooltip>
      </Box>
      <Stack spacing={1}>
        {seedUrls.map((url, idx) => (
          <Typography key={idx} variant="body2" sx={{ wordBreak: 'break-all' }}>{url}</Typography>
        ))}
      </Stack>
    </Paper>
  );
} 