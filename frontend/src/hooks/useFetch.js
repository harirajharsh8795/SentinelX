import { useEffect, useState } from "react";
import api from "../services/api.js";
import { useStore } from "../store/useStore.js";

export default function useFetch(path, initialData) {
  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const selectedDocId = useStore((state) => state.selectedDocId);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    api
      .get(path)
      .then((response) => {
        if (!isMounted) return;
        setData(response.data);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err?.response?.data?.detail || "Failed to load data");
      })
      .finally(() => {
        if (!isMounted) return;
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [path, selectedDocId]);

  return { data, loading, error };
}
