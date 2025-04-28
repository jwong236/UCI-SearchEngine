import { useState, useEffect } from 'react';
import { crawlerApi } from '../api/crawler';

export function useCrawlerStats() {
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await crawlerApi.getStatus();
        setStats(data.statistics);
      } catch (error) {
        console.error('Failed to fetch statistics:', error);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 5000);

    return () => clearInterval(interval);
  }, []);

  return {
    stats
  };
} 