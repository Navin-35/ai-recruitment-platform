import api from "./api";

export const uploadResume = async (candidateId, file) => {
  const formData = new FormData();
  formData.append("candidate_id", candidateId);
  formData.append("file", file);

  const response = await api.post("/resumes/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

export const processResume = async (resumeId) => {
  const response = await api.post(`/resumes/${resumeId}/process`);
  return response.data;
};

export const getResumesByCandidate = async (candidateId) => {
  const response = await api.get(`/resumes/candidate/${candidateId}`);
  return response.data;
};

export const getResumeSignedUrl = async (resumeId, expiresIn = 3600) => {
  const response = await api.get(`/resumes/${resumeId}/signed-url`, {
    params: { expires_in: expiresIn },
  });
  return response.data;
};

export const deleteResume = async (resumeId) => {
  const response = await api.delete(`/resumes/${resumeId}`);
  return response.data;
};
