import { AppBar, Toolbar, Tabs, Tab, Typography, Box } from '@mui/material';
import { Link } from 'react-router-dom';

interface NavbarProps {
  currentTab: number;
  onTabChange: (event: React.SyntheticEvent, newValue: number) => void;
}

export function Navbar({ currentTab, onTabChange }: NavbarProps) {
  return (
    <AppBar position="static" elevation={0}>
      <Toolbar sx={{ minHeight: 64, position: 'relative', px: 0, width: '100%' }}>
        {/* Centered Title */}
        <Box sx={{ position: 'absolute', left: 0, right: 0, display: 'flex', justifyContent: 'center', pointerEvents: 'none' }}>
          <Typography 
            variant="h5" 
            sx={{
              color: 'white',
              fontWeight: 700,
              letterSpacing: 2,
              textShadow: '0 2px 8px rgba(0,0,0,0.08)',
              pointerEvents: 'auto',
              userSelect: 'none',
            }}
          >
            UCI Search & Scrape
          </Typography>
        </Box>
        {/* Tabs aligned right */}
        <Box sx={{ flexGrow: 1 }} />
        <Tabs 
          value={currentTab} 
          onChange={onTabChange}
          sx={{
            ml: 'auto',
            '& .MuiTab-root': {
              color: 'rgba(255, 255, 255, 0.7)',
              fontSize: '1rem',
              textTransform: 'none',
              minHeight: 64,
              minWidth: 120,
              '&.Mui-selected': {
                color: 'secondary.main',
              },
            },
            '& .MuiTabs-indicator': {
              backgroundColor: 'secondary.main',
            },
          }}
        >
          <Tab label="Search" component={Link} to="/" />
          <Tab label="Crawler" component={Link} to="/crawler" />
          <Tab label="Statistics" component={Link} to="/statistics" />
        </Tabs>
        {/* UCI Icon on far right */}
        <Box sx={{ ml: 2, display: 'flex', alignItems: 'center' }}>
          <img src="/uci-icon-2.png" alt="UCI Logo" style={{ height: 40, width: 'auto', display: 'block' }} />
        </Box>
      </Toolbar>
    </AppBar>
  );
} 