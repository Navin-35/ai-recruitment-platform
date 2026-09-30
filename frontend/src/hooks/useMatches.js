import { useState, useEffect, useCallback } from "react";
import { getJobMatches, rankCandidatesForJob } from "../services/matches";

export const useJobMatches = (jobId) => {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [ranking, setRanking] = useState(false);
  const [error, setError] = useState(null);

  const fetchMatches = useCallback(async () => {
    if (!jobId) return;
    try {
      setLoading(true);
      setError(null);
      const data = await getJobMatches(jobId);
      setMatches(data);
    } catch (err) {
      setError(err.message || "Failed to load candidate matches");
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  const triggerRanking = async () => {
    if (!jobId) return;
    try {
      setRanking(true);
      setError(null);
      const rankedData = await rankCandidatesForJob(jobId);
      setMatches(rankedData);
      return rankedData;
    } catch (err) {
      setError(err.message || "Failed to execute candidate ranking");
      throw err;
    } finally {
      setRanking(false);
    }
  };

  useEffect(() => {
    fetchMatches();
  }, [fetchMatches]);

  return { matches, loading, ranking, error, refetch: fetchMatches, triggerRanking };
};
