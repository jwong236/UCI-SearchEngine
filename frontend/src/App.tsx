import { ThemeProvider } from '@mui/material';
import CssBaseline from '@mui/material/CssBaseline';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Search } from './pages/Search';
import { Crawler } from './pages/Crawler';
import { Statistics } from './pages/Statistics';
import { Layout } from './components/Layout';
import { theme } from './theme';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Search />} />
            <Route path="/crawler" element={<Crawler />} />
            <Route path="/statistics" element={<Statistics />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App;
