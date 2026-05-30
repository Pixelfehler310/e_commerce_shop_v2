import { Module } from '@nestjs/common';
import { HealthController } from './common/health/health.controller';
import { BillingChargesController } from './modules/charges/controllers/billing-charges.controller';
import { BillingRefundsController } from './modules/refunds/controllers/billing-refunds.controller';
import { BillingSimulationController } from './modules/simulation/controllers/billing-simulation.controller';
import { BillingWebhooksController } from './modules/webhooks/controllers/billing-webhooks.controller';

@Module({
  controllers: [
    HealthController,
    BillingChargesController,
    BillingRefundsController,
    BillingSimulationController,
    BillingWebhooksController
  ]
})
export class AppModule {}