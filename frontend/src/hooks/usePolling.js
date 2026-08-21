import { useEffect, useRef } from 'react';

/**
 * Custom hook for executing polling callbacks at a specified interval.
 */
export function usePolling(callback, delay, enabled = true) {
  const savedCallback = useRef(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (!enabled || delay === null || delay === undefined) {
      return;
    }

    const tick = () => {
      savedCallback.current();
    };

    const id = setInterval(tick, delay);
    return () => clearInterval(id);
  }, [delay, enabled]);
}
