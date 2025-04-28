import React, { useState } from 'react';
import { crawlerApi } from '../api/crawler';

const SEED_URLS = [
  'https://www.ics.uci.edu',
  'https://www.cs.uci.edu',
  'https://www.informatics.uci.edu',
  'https://www.stat.uci.edu',
];

export function useCrawlerForm() {
  const [status, setStatus] = useState<'idle' | 'loading' | 'running' | 'stopped' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [failedUrls, setFailedUrls] = useState<any[] | null>(null);
  const [failedLoading, setFailedLoading] = useState(false);
  const [secretKey, setSecretKey] = useState('');

  // Manual fetch for status/statistics
  const fetchStats = async () => {
    try {
      const data = await crawlerApi.getStatus();
      setIsRunning(data.is_running);
      setStats(data.statistics);
      setStatus(data.is_running ? 'running' : 'stopped');
    } catch (error) {
      setStatus('error');
      setMessage('Failed to fetch crawler status.');
    }
  };

  // Fetch once on mount
  React.useEffect(() => {
    fetchStats();
    // eslint-disable-next-line
  }, []);

  const handleStart = async () => {
    if (!secretKey) {
      setMessage('Secret key is required to start the crawler.');
      setStatus('error');
      return;
    }
    setStatus('loading');
    setMessage('');
    try {
      await crawlerApi.start(secretKey);
      setStatus('running');
      setMessage('Crawler started successfully!');
      setIsRunning(true);
      fetchStats();
    } catch (error) {
      setStatus('error');
      setMessage('Failed to start crawler.');
    }
  };

  const handleStop = async () => {
    if (!secretKey) {
      setMessage('Secret key is required to stop the crawler.');
      setStatus('error');
      return;
    }
    setStatus('loading');
    setMessage('');
    try {
      await crawlerApi.stop(secretKey);
      setStatus('stopped');
      setMessage('Crawler stopped successfully!');
      setIsRunning(false);
      fetchStats();
    } catch (error) {
      setStatus('error');
      setMessage('Failed to stop crawler.');
    }
  };

  const handleShowFailedUrls = async () => {
    setFailedLoading(true);
    setMessage('');
    try {
      const data = await crawlerApi.getFailedUrls();
      setFailedUrls(data);
      setFailedLoading(false);
    } catch (error) {
      setMessage('Failed to fetch failed URLs.');
      setFailedLoading(false);
    }
  };

  return {
    SEED_URLS,
    status,
    message,
    isRunning,
    stats,
    failedUrls,
    failedLoading,
    handleStart,
    handleStop,
    handleShowFailedUrls,
    setFailedUrls,
    fetchStats,
    secretKey,
    setSecretKey,
  };
} 