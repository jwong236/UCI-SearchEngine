import { Box, Container, GlobalStyles } from '@mui/material';
import { ReactNode } from 'react';
import { Navbar } from './Navbar';
import { useTabNavigation } from '../hooks/useTabNavigation';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { currentTab, handleTabChange } = useTabNavigation();

  return (
    <>
      <GlobalStyles
        styles={{
          html: {
            width: '100%',
            height: '100%',
          },
          body: {
            width: '100%',
            height: '100%',
          },
          '#root': {
            width: '100%',
            height: '100%',
          },
        }}
      />
      <Box sx={{ 
        display: 'flex', 
        flexDirection: 'column', 
        minHeight: '100vh',
        width: '100%'
      }}>
        <Navbar currentTab={currentTab} onTabChange={handleTabChange} />
        <Box 
          component="main" 
          sx={{ 
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            py: 6,
            px: 3,
            bgcolor: '#f5f5f5',
            width: '100%'
          }}
        >
          <Container 
            maxWidth="lg"
            sx={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              width: '100%'
            }}
          >
            {children}
          </Container>
        </Box>
      </Box>
    </>
  );
} 