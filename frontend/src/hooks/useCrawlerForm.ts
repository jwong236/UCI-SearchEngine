import React, { useState, useEffect, useCallback } from 'react';
import { crawlerApi, CrawlerStatus } from '../api/crawler';

const SEED_URLS = [
  'https://www.ics.uci.edu',
  'https://www.cs.uci.edu',
  'https://www.informatics.uci.edu',
  'https://www.stat.uci.edu',
];

export type CrawlMode = 'fresh' | 'continue' | 'recrawl';

interface UseCrawlerFormProps {
  secretKey: string;
}

export function useCrawlerForm({ secretKey }: UseCrawlerFormProps) {
  const [status, setStatus] = useState<'idle' | 'loading' | 'running' | 'stopped' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [crawlerData, setCrawlerData] = useState<CrawlerStatus | null>(null);
  const [failedUrls, setFailedUrls] = useState<any[] | null>(null);
  const [failedLoading, setFailedLoading] = useState(false);
  const [crawlMode, setCrawlMode] = useState<CrawlMode>('fresh');
  const [currentSeedUrls, setCurrentSeedUrls] = useState<string[]>(SEED_URLS);

  const refreshCrawlerStatus = useCallback(async () => {
    try {
      const data = await crawlerApi.getStatus();
      setCrawlerData(data);
      setStatus(data.status === 'running' ? 'running' : 'stopped');
      return data;
    } catch (error) {
      setStatus('error');
      setMessage('Failed to fetch crawler status.');
      return null;
    }
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
      await crawlerApi.start(secretKey, crawlMode, currentSeedUrls);
      await refreshCrawlerStatus();
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
      await refreshCrawlerStatus();
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
      setFailedUrls(data.failed_urls);
      setFailedLoading(false);
    } catch (error) {
      setMessage('Failed to fetch failed URLs.');
      setFailedLoading(false);
    }
  };

  useEffect(() => {
    refreshCrawlerStatus();
  }, [refreshCrawlerStatus]);

  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval>;
    if (status === 'running') {
      intervalId = setInterval(refreshCrawlerStatus, 5000);
    }
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [status, refreshCrawlerStatus]);

  return {
    SEED_URLS,
    currentSeedUrls,
    setCurrentSeedUrls,
    status,
    message,
    setMessage,
    isRunning: status === 'running',
    stats: crawlerData?.statistics,
    failedUrls,
    failedLoading,
    handleStart,
    handleStop,
    handleShowFailedUrls,
    setFailedUrls,
    refreshStats: refreshCrawlerStatus,
    crawlMode,
    setCrawlMode,
  };
} 