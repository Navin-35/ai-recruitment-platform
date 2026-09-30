import api from "./api";

export const matchCandidateToJob = async (jobId, candidateId, weights = null) => {
  const payload = {
    job_id: jobId,
    candidate_id: candidateId,
  };
  if (weights) {
    payload.weights = weights;
  }
  const response = await api.post("/matches/", payload);
  return response.data;
};

export const getJobMatches = async (jobId) => {
  const response = await api.get(`/matches/job/${jobId}`);
  return response.data;
};

export const rankCandidatesForJob = async (jobId) => {
  const response = await api.post(`/matches/job/${jobId}/rank`);
  return response.data;
};

export const getSystemStatus = async () => {
  const response = await api.get("/api/system/status");
  return response.data;
};

export const getTaskStatus = async (taskId) => {
  const response = await api.get(`/tasks/${taskId}`);
  return response.data;
};
