import axios from 'axios';

const BASE = process.env.REACT_APP_API_URL || '/api';

const api = axios.create({ baseURL: BASE, timeout: 15000 });

export const fetchTenders = (params) =>
  api.get('/tenders', { params }).then(r => r.data);

export const fetchTender = (id) =>
  api.get(`/tenders/${id}`).then(r => r.data);

export const fetchStats = () =>
  api.get('/stats').then(r => r.data);

export const fetchFilters = () =>
  api.get('/filters').then(r => r.data);

export const fetchScrapeRuns = () =>
  api.get('/scrape-runs').then(r => r.data);
