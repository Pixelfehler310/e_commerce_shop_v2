import { Controller, Get } from '@nestjs/common';

type ServiceHealthStatus = 'UP' | 'DOWN';

interface HealthTarget {
  key: string;
  name: string;
  baseUrl: string;
}

interface ServiceHealthResult {
  key: string;
  name: string;
  url: string;
  status: ServiceHealthStatus;
  checkedAt: string;
  latencyMs: number;
  httpStatus?: number;
  detail?: unknown;
  error?: string;
}

interface ServiceHealthOverview {
  checkedAt: string;
  services: ServiceHealthResult[];
}

const healthTimeoutMs = 2500;

@Controller('v1/admin/health')
export class ServiceHealthController {
  @Get('services')
  async getServiceHealth(): Promise<ServiceHealthOverview> {
    const checkedAt = new Date().toISOString();
    const services = await Promise.all(this.getTargets().map((target) => this.checkTarget(target, checkedAt)));

    return {
      checkedAt,
      services
    };
  }

  private getTargets(): HealthTarget[] {
    const localShopUrl = `http://127.0.0.1:${process.env.PORT ?? 3000}`;

    return [
      {
        key: 'shop-service',
        name: 'Shop-Service',
        baseUrl: process.env.SHOP_BASE_URL ?? localShopUrl
      },
      {
        key: 'warehouse-service',
        name: 'Warehouse-Service',
        baseUrl: process.env.WAREHOUSE_BASE_URL ?? 'http://warehouse-service:3000'
      },
      {
        key: 'billing-service',
        name: 'Billing-Service',
        baseUrl: process.env.BILLING_BASE_URL ?? 'http://billing-service:3000'
      },
      {
        key: 'invoice-service',
        name: 'Invoice-Service',
        baseUrl: process.env.INVOICE_BASE_URL ?? 'http://invoice-service:3000'
      },
      {
        key: 'audit-service',
        name: 'Audit-Service',
        baseUrl: process.env.AUDIT_BASE_URL ?? 'http://audit-service:3000'
      }
    ];
  }

  private async checkTarget(target: HealthTarget, checkedAt: string): Promise<ServiceHealthResult> {
    const startedAt = Date.now();
    const url = `${target.baseUrl.replace(/\/$/, '')}/health`;
    const abortController = new AbortController();
    const timeout = setTimeout(() => abortController.abort(), healthTimeoutMs);

    try {
      const response = await fetch(url, { signal: abortController.signal });
      const detail = await this.readResponseBody(response);

      return {
        key: target.key,
        name: target.name,
        url,
        status: response.ok ? 'UP' : 'DOWN',
        checkedAt,
        latencyMs: Date.now() - startedAt,
        httpStatus: response.status,
        detail
      };
    } catch (error) {
      return {
        key: target.key,
        name: target.name,
        url,
        status: 'DOWN',
        checkedAt,
        latencyMs: Date.now() - startedAt,
        error: this.getErrorMessage(error)
      };
    } finally {
      clearTimeout(timeout);
    }
  }

  private async readResponseBody(response: Response): Promise<unknown> {
    const contentType = response.headers.get('content-type') ?? '';

    if (contentType.includes('application/json')) {
      return response.json();
    }

    return response.text();
  }

  private getErrorMessage(error: unknown): string {
    if (error instanceof Error) {
      return error.name === 'AbortError' ? 'Health check timed out' : error.message;
    }

    return 'Health check failed';
  }
}