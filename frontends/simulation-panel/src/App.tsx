import { useCallback, useEffect, useMemo, useState } from 'react';

type ServiceStatus = 'UP' | 'DOWN';

interface ServiceHealthResult {
  key: string;
  name: string;
  url: string;
  status: ServiceStatus;
  checkedAt: string;
  latencyMs: number;
  httpStatus?: number;
  error?: string;
}

interface ServiceHealthOverview {
  checkedAt: string;
  services: ServiceHealthResult[];
}

const shopApiBaseUrl = import.meta.env.VITE_SHOP_API_BASE_URL ?? 'http://localhost:3000';

export function App(): JSX.Element {
  const [overview, setOverview] = useState<ServiceHealthOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadHealth = useCallback(async () => {
    setLoading(true);

    try {
      const response = await fetch(`${shopApiBaseUrl}/v1/admin/health/services`);

      if (!response.ok) {
        throw new Error(`Gateway returned ${response.status}`);
      }

      const nextOverview = (await response.json()) as ServiceHealthOverview;
      setOverview(nextOverview);
      setError(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Gateway unavailable');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadHealth();
    const interval = window.setInterval(() => void loadHealth(), 10000);

    return () => window.clearInterval(interval);
  }, [loadHealth]);

  const summary = useMemo(() => {
    const services = overview?.services ?? [];
    const online = services.filter((service) => service.status === 'UP').length;

    return {
      total: services.length,
      online,
      offline: services.length - online
    };
  }, [overview]);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Simulation Panel</p>
          <h1>Service Health</h1>
        </div>
        <button className="refresh-button" type="button" onClick={() => void loadHealth()} disabled={loading}>
          {loading ? 'Checking' : 'Refresh'}
        </button>
      </header>

      <section className="summary-grid" aria-label="Health summary">
        <Metric label="Services" value={summary.total.toString()} />
        <Metric label="Online" value={summary.online.toString()} tone="good" />
        <Metric label="Offline" value={summary.offline.toString()} tone={summary.offline > 0 ? 'bad' : 'neutral'} />
        <Metric label="Checked" value={formatCheckedAt(overview?.checkedAt)} />
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="service-grid" aria-label="Expected services">
        {(overview?.services ?? []).map((service) => (
          <article className="service-card" key={service.key}>
            <div className="service-card__header">
              <div>
                <h2>{service.name}</h2>
                <p>{service.url}</p>
              </div>
              <span className={`status-pill status-pill--${service.status.toLowerCase()}`}>
                <span aria-hidden="true" />
                {service.status === 'UP' ? 'Online' : 'Offline'}
              </span>
            </div>
            <dl className="service-facts">
              <div>
                <dt>HTTP</dt>
                <dd>{service.httpStatus ?? '-'}</dd>
              </div>
              <div>
                <dt>Latency</dt>
                <dd>{service.latencyMs} ms</dd>
              </div>
              <div>
                <dt>Last Check</dt>
                <dd>{formatCheckedAt(service.checkedAt)}</dd>
              </div>
            </dl>
            {service.error ? <p className="service-error">{service.error}</p> : null}
          </article>
        ))}
      </section>
    </main>
  );
}

interface MetricProps {
  label: string;
  value: string;
  tone?: 'neutral' | 'good' | 'bad';
}

function Metric({ label, value, tone = 'neutral' }: MetricProps): JSX.Element {
  return (
    <div className={`metric metric--${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatCheckedAt(value: string | undefined): string {
  if (!value) {
    return '-';
  }

  return new Intl.DateTimeFormat('de-DE', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(new Date(value));
}