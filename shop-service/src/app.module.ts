import { Module } from '@nestjs/common';
import { HealthController } from './common/health/health.controller';
import { AdminController } from './modules/admin/controllers/admin.controller';
import { ServiceHealthController } from './modules/admin/controllers/service-health.controller';
import { AuthController } from './modules/auth/controllers/auth.controller';
import { BasketController } from './modules/basket/controllers/basket.controller';
import { OrdersController } from './modules/orders/controllers/orders.controller';
import { ProductsController } from './modules/products/controllers/products.controller';
import { MeController } from './modules/users/controllers/me.controller';

@Module({
  controllers: [
    HealthController,
    AdminController,
    ServiceHealthController,
    AuthController,
    BasketController,
    OrdersController,
    ProductsController,
    MeController
  ]
})
export class AppModule {}