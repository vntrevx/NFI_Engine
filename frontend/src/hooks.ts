import { useCallback, useEffect, useState } from "react";

import type { AsyncState } from "./types";

export function useAsyncResource<T>(loader: () => Promise<T>, fallback: T, refreshMs = 0): AsyncState<T> {
  const [state, setState] = useState<AsyncState<T>>({
    data: fallback,
    loading: true,
    error: null,
  });

  useEffect(() => {
    let active = true;
    const load = (): void => {
      if (document.visibilityState === "hidden") {
        return;
      }
      loader()
        .then((data) => {
          if (active) {
            setState({ data, loading: false, error: null });
          }
        })
        .catch((error: unknown) => {
          if (active) {
            setState((current) => ({
              data: current.data ?? fallback,
              loading: false,
              error: error instanceof Error ? error.message : "request failed",
            }));
          }
        });
    };

    load();
    const intervalId = refreshMs > 0 ? window.setInterval(load, refreshMs) : undefined;
    return () => {
      active = false;
      if (intervalId !== undefined) {
        window.clearInterval(intervalId);
      }
    };
  }, [fallback, loader, refreshMs]);

  return state;
}

export function useActionState(initial = "idle"): {
  state: string;
  run: (action: () => Promise<unknown>) => Promise<void>;
  setState: (state: string) => void;
} {
  const [state, setState] = useState(initial);
  const run = useCallback(async (action: () => Promise<unknown>) => {
    setState("pending");
    try {
      const result = await action();
      setState(JSON.stringify(result, null, 2).slice(0, 900));
    } catch (error: unknown) {
      setState(error instanceof Error ? error.message : "request failed");
    }
  }, []);
  return { state, run, setState };
}
