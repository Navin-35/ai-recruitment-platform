import { useState, useEffect, useCallback } from "react";
import { getCandidates, getCandidate } from "../services/candidates";

export const useCandidates = (search = "") => {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchCandidates = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {};
      if (search) params.search = search;
      const data = await getCandidates(params);
      setCandidates(data);
    } catch (err) {
      setError(err.message || "Failed to load candidates");
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    fetchCandidates();
  }, [fetchCandidates]);

  return { candidates, loading, error, refetch: fetchCandidates };
};

export const useCandidate = (candidateId) => {
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchCandidate = useCallback(async () => {
    if (!candidateId) return;
    try {
      setLoading(true);
      setError(null);
      const data = await getCandidate(candidateId);
      setCandidate(data);
    } catch (err) {
      setError(err.message || "Failed to load candidate profile");
    } finally {
      setLoading(false);
    }
  }, [candidateId]);

  useEffect(() => {
    fetchCandidate();
  }, [fetchCandidate]);

  return { candidate, loading, error, refetch: fetchCandidate };
};
