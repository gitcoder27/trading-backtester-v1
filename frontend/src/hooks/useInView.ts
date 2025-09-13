import { useEffect, useRef, useState } from 'react';

interface UseInViewOptions {
  root?: Element | null;
  rootMargin?: string;
  threshold?: number | number[];
  once?: boolean;
}

export function useInView<T extends HTMLElement = HTMLDivElement>(options: UseInViewOptions = {}) {
  const ref = useRef<T | null>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (entry.isIntersecting) {
          setInView(true);
          if (options.once !== false) observer.unobserve(entry.target);
        } else if (!options.once) {
          setInView(false);
        }
      },
      {
        root: options.root || null,
        rootMargin: options.rootMargin || '0px 0px -10% 0px',
        threshold: options.threshold ?? 0,
      }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [options.root, options.rootMargin, options.threshold, options.once]);

  return { ref, inView } as const;
}

