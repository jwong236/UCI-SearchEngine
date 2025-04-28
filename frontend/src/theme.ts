import { createTheme } from '@mui/material';

export const theme = createTheme({
  palette: {
    primary: {
      main: '#0C2340', // UCI Dark Blue
    },
    secondary: {
      main: '#FFC72C', // UCI Yellow
    },
  },
  typography: {
    fontFamily: '"Segoe UI", "Helvetica Neue", Arial, sans-serif',
    h3: {
      fontWeight: 500,
    },
    h4: {
      fontWeight: 500,
    },
    h6: {
      fontWeight: 500,
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        '#root': {
          display: 'flex',
          flexDirection: 'column',
          minHeight: '100vh',
          width: '100%',
        },
        body: {
          margin: 0,
          padding: 0,
          width: '100%',
          minHeight: '100vh',
        },
      },
    },
  },
}); 