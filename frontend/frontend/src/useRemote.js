import { useEffect, useState } from "react";
import { errorText, request } from "./api";

export function useRemote(path, params, enabled = true) {
  const [version, setVersion] = useState(0);
  const [result, setResult] = useState(null);
  const query = JSON.stringify(params || {});
  const key = `${path}:${query}:${version}`;
  useEffect(() => {
    if (!enabled) return;
    let active = true;
    request(path, "get", undefined, JSON.parse(query))
      .then((data) => { if (active) setResult({ key, data }); })
      .catch((error) => { if (active) setResult({ key, error: errorText(error) }); });
    return () => { active = false; };
  }, [enabled, key, path, query]);
  const current = enabled && result?.key === key ? result : null;
  function updateData(values) {
    setResult((previous) => previous?.key === key && previous.data
      ? { key, data: { ...previous.data, ...values } } : previous);
  }
  return { ...current, loading: enabled && !current, reload: () => setVersion((value) => value + 1), updateData };
}
