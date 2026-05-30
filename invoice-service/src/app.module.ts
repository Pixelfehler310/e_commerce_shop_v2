import { Module } from '@nestjs/common';
import { HealthController } from './common/health/health.controller';
import { InvoiceEventsController } from './modules/events/controllers/invoice-events.controller';

@Module({
  controllers: [HealthController, InvoiceEventsController]
})
export class AppModule {}