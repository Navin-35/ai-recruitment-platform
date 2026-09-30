import api from "./api";

export const getJobs = async (params = {}) => {
  const response = await api.get("/jobs/", { params });
  return response.data;
};

export const getJob = async (jobId) => {
  const response = await api.get(`/jobs/${jobId}`);
  return response.data;
};

export const createJob = async (jobData) => {
  const response = await api.post("/jobs/", jobData);
  return response.data;
};

export const uploadJobFile = async (formData) => {
  const response = await api.post("/jobs/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

export const updateJob = async (jobId, updateData) => {
  const response = await api.put(`/jobs/${jobId}`, updateData);
  return response.data;
};

export const deleteJob = async (jobId) => {
  const response = await api.delete(`/jobs/${jobId}`);
  return response.data;
};

export const extractJobRequirements = async (jobId) => {
  const response = await api.post(`/jobs/${jobId}/extract-requirements`);
  return response.data;
};
