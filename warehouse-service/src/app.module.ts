import { Module } from '@nestjs/common';
import { HealthController } from './common/health/health.controller';
import { WarehouseBookingsController } from './modules/bookings/controllers/warehouse-bookings.controller';
import { WarehouseProductsController } from './modules/products/controllers/warehouse-products.controller';
import { WarehouseReservationsController } from './modules/reservations/controllers/warehouse-reservations.controller';
import { WarehouseSimulationController } from './modules/simulation/controllers/warehouse-simulation.controller';

@Module({
  controllers: [
    HealthController,
    WarehouseBookingsController,
    WarehouseProductsController,
    WarehouseReservationsController,
    WarehouseSimulationController
  ]
})
export class AppModule {}