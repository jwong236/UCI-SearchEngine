import React, { useState } from 'react';
import { crawlerApi, CrawlerStatus } from '../api/crawler';

const SEED_URLS = [
  'https://www.ics.uci.edu',
  'https://www.cs.uci.edu',
  'https://www.informatics.uci.edu',
  'https://www.stat.uci.edu',
];

export type CrawlMode = 'fresh' | 'continue' | 'recrawl';

export function useCrawlerForm() {
  const [status, setStatus] = useState<'idle' | 'loading' | 'running' | 'stopped' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [crawlerData, setCrawlerData] = useState<CrawlerStatus | null>(null);
  const [failedUrls, setFailedUrls] = useState<any[] | null>(null);
  const [failedLoading, setFailedLoading] = useState(false);
  const [secretKey, setSecretKey] = useState('');
  const [crawlMode, setCrawlMode] = useState<CrawlMode>('continue');

  const fetchStats = async () => {
    try {
      const data = await crawlerApi.getStatus();
      setCrawlerData(data);
      setStatus(data.status === 'running' ? 'running' : 'stopped');
    } catch (error) {
      setStatus('error');
      setMessage('Failed to fetch crawler status.');
    }
  };

  const handleStart = async () => {
    if (!secretKey) {
      setMessage('Secret key is required to start the crawler.');
      setStatus('error');
      return;
    }
    setStatus('loading');
    setMessage('');
    try {
      await crawlerApi.start(secretKey, crawlMode);
      setStatus('running');
      setMessage('Crawler started successfully!');
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
    isRunning: crawlerData?.status === 'running',
    stats: crawlerData?.statistics,
    failedUrls,
    failedLoading,
    handleStart,
    handleStop,
    handleShowFailedUrls,
    setFailedUrls,
    refreshStats: fetchStats,
    secretKey,
    setSecretKey,
    crawlMode,
    setCrawlMode,
  };
} 