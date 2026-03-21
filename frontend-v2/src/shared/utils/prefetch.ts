type ResourceType = 'prefetch' | 'preload' | 'dns-prefetch' | 'preconnect';

interface PreloadOptions {
  as?: 'script' | 'style' | 'image' | 'font' | 'fetch';
  type?: string;
  crossorigin?: boolean;
}

class ResourcePrefetcher {
  private prefetchedUrls = new Set<string>();

  prefetch(url: string, options?: PreloadOptions): void {
    if (this.prefetchedUrls.has(url)) return;
    this.prefetchedUrls.add(url);

    this.createLinkElement('prefetch', url, options);
  }

  preload(url: string, options?: PreloadOptions): void {
    if (this.prefetchedUrls.has(url)) return;
    this.prefetchedUrls.add(url);

    this.createLinkElement('preload', url, options);
  }

  dnsPrefetch(domain: string): void {
    this.createLinkElement('dns-prefetch', `//${domain}`);
  }

  preconnect(url: string): void {
    this.createLinkElement('preconnect', url);
  }

  private createLinkElement(
    type: ResourceType,
    href: string,
    options?: PreloadOptions
  ): void {
    if (typeof document === 'undefined') return;

    const link = document.createElement('link');
    link.rel = type;
    link.href = href;

    if (options?.as) {
      link.as = options.as;
    }
    if (options?.type) {
      link.type = options.type;
    }
    if (options?.crossorigin) {
      link.crossOrigin = 'anonymous';
    }

    document.head.appendChild(link);
  }

  prefetchRoutes(routes: string[]): void {
    routes.forEach(route => {
      this.prefetch(route);
    });
  }

  prefetchImages(urls: string[]): void {
    urls.forEach(url => {
      this.prefetch(url, { as: 'image' });
    });
  }

  prefetchFonts(urls: string[]): void {
    urls.forEach(url => {
      this.prefetch(url, { as: 'font' });
    });
  }
}

export const resourcePrefetcher = new ResourcePrefetcher();

export function prefetchOnHover(selector: string, getUrl: (el: HTMLElement) => string): void {
  if (typeof document === 'undefined') return;

  const handler = (event: MouseEvent) => {
    const target = event.target as HTMLElement;
    const element = target.closest(selector);
    if (element) {
      const url = getUrl(element);
      resourcePrefetcher.prefetch(url);
    }
  };

  document.addEventListener('mouseover', handler, { passive: true });
}

export function prefetchVisibleLinks(
  container: HTMLElement,
  selector: string,
  getUrl: (el: HTMLElement) => string
): void {
  if (typeof IntersectionObserver === 'undefined') return;

  const observer = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const element = entry.target as HTMLElement;
          const url = getUrl(element);
          resourcePrefetcher.prefetch(url);
          observer.unobserve(element);
        }
      });
    },
    { rootMargin: '100px' }
  );

  const elements = container.querySelectorAll(selector);
  elements.forEach(el => observer.observe(el));
}
