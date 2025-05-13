import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export interface CrawlerStatus {
  status: 'running' | 'stopped';
  statistics: {
    urls_crawled: number;
    urls_failed: number;
    urls_in_queue: number;
  };
}

export interface DetailedStatistics {
  crawler_statistics: {
    status: 'running' | 'stopped';
    urls_crawled: number;
    urls_failed: number;
    unique_domains: number;
    urls_in_queue: number;
  };
  database_statistics: {
    total_documents: number;
    total_terms: number;
    total_index_entries: number;
  };
}

export const crawlerApi = {
  start: async (secretKey: string, mode: 'fresh' | 'continue' | 'recrawl', seedUrls: string[]) => {
    const response = await axios.post(`${API_BASE_URL}/crawler/start`, seedUrls, {
      headers: { 'X-Secret-Key': secretKey },
      params: { mode }
    });
    return response.data;
  },

  stop: async (secretKey: string) => {
    const response = await axios.post(`${API_BASE_URL}/crawler/stop`, null, {
      headers: { 'X-Secret-Key': secretKey }
    });
    return response.data;
  },

  getStatus: async (): Promise<CrawlerStatus> => {
    const response = await axios.get(`${API_BASE_URL}/crawler/status`);
    return response.data;
  },

  getDetailedStatistics: async (): Promise<DetailedStatistics> => {
    const response = await axios.get(`${API_BASE_URL}/crawler/statistics`);
    return response.data;
  },

  getFailedUrls: async () => {
    const response = await axios.get(`${API_BASE_URL}/crawler/failed-urls`);
    return response.data;
  }
}; 