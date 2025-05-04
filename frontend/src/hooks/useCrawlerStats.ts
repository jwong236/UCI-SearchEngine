import { useState, useEffect } from 'react';
import { DetailedStatistics } from '../api/crawler';
import { useCrawlerForm } from './useCrawlerForm';

export function useCrawlerStats() {
  const { stats } = useCrawlerForm();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (stats) {
      setLoading(false);
      setError(null);
    }
  }, [stats]);

  return { stats, loading, error };
} 