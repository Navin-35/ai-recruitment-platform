import api from "./api";

export const getCandidates = async (params = {}) => {
  const response = await api.get("/candidates/", { params });
  return response.data;
};

export const getCandidate = async (candidateId) => {
  const response = await api.get(`/candidates/${candidateId}`);
  return response.data;
};

export const createCandidate = async (candidateData) => {
  const response = await api.post("/candidates/", candidateData);
  return response.data;
};

export const deleteCandidate = async (candidateId) => {
  const response = await api.delete(`/candidates/${candidateId}`);
  return response.data;
};
