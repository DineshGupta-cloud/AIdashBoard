import axios from "axios";

const API_BASE = "http://127.0.0.1:8000";

export const getAnalysis = async () => {
  const res = await axios.get(`${API_BASE}/options/analyze`);
  return res.data;
};

export const getChartData = async () => {
  const res = await axios.get(`${API_BASE}/options/chart`);
  console.log("Chart Data:", res.data);
  return res.data;
};

export const searchRag = async (query) => {
  const res = await axios.get(`${API_BASE}/rag/search?q=${query}`);
  return res.data?.results || [];
};

export const fetchOptionChainTable = async () => {
  const res = await axios.get(`${API_BASE}/options/table`);
  return res.data;
};
export const getSignals = async () => {
  const res = await axios.get(`${API_BASE}/options/signals`);
  // console.log("Signals Data:", res.data);
  return res.data;
};

export const advancedGetSignals = async () => {
  const res = await axios.get(`${API_BASE}/options/advanced-advisor`);
  console.log("Signals Data:", res.data);
  return res.data;
};


export const getBankNiftyData = async () => {
  const response = await axios.get(`${API_BASE}/options/banknifty`);
  console.log("BankNifty Data:", response.data);
  return response.data;
};

export const getAlerts = async () => (await axios.get(`${API_BASE}/alerts`)).data.alerts;
export const createAlert = async (alert) => (await axios.post(`${API_BASE}/alerts`, alert)).data;
export const setAlertEnabled = async (id, enabled) => (await axios.patch(`${API_BASE}/alerts/${id}`, { enabled })).data;
export const removeAlert = async (id) => axios.delete(`${API_BASE}/alerts/${id}`);
export const evaluateAlerts = async () => (await axios.post(`${API_BASE}/alerts/evaluate`)).data;
export const getMarketStatus = async () => (await axios.get(`${API_BASE}/market/status`)).data;
