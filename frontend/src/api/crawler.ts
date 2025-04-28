import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export interface CrawlerStatus {
  is_running: boolean;
  statistics: {
    urls_crawled: number;
    urls_failed: number;
    unique_domains: number;
  };
}

export const crawlerApi = {
  start: async (secretKey: string) => {
    const response = await axios.post(`${API_BASE_URL}/crawler/start`, null, {
      params: { secret_key: secretKey }
    });
    return response.data;
  },

  stop: async (secretKey: string) => {
    const response = await axios.post(`${API_BASE_URL}/crawler/stop`, null, {
      params: { secret_key: secretKey }
    });
    return response.data;
  },

  getStatus: async (): Promise<CrawlerStatus> => {
    const response = await axios.get(`${API_BASE_URL}/crawler/status`);
    return response.data;
  },

  getFailedUrls: async () => {
    const response = await axios.get(`${API_BASE_URL}/crawler/failed-urls`);
    return response.data;
  }
}; 