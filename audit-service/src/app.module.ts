import { Module } from '@nestjs/common';
import { HealthController } from './common/health/health.controller';
import { AuditEventsController } from './modules/events/controllers/audit-events.controller';
import { AuditOrdersController } from './modules/orders/controllers/audit-orders.controller';
import { AuditSearchController } from './modules/search/controllers/audit-search.controller';
import { AuditSnapshotsController } from './modules/snapshots/controllers/audit-snapshots.controller';
import { AuditStreamController } from './modules/stream/controllers/audit-stream.controller';

@Module({
  controllers: [
    HealthController,
    AuditEventsController,
    AuditOrdersController,
    AuditSearchController,
    AuditSnapshotsController,
    AuditStreamController
  ]
})
export class AppModule {}