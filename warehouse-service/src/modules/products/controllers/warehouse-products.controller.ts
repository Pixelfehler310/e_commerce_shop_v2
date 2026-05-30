import { Body, Controller, Get, NotImplementedException, Param, Patch, Post } from '@nestjs/common';

@Controller('v1/warehouse/products')
export class WarehouseProductsController {
  @Post()
  initializeProductStock(@Body() request: unknown): never {
    throw new NotImplementedException('Contract stub only');
  }

  @Patch(':productId/stock')
  adjustStock(@Param('productId') productId: string, @Body() request: unknown): never {
    throw new NotImplementedException('Contract stub only');
  }

  @Get(':productId/stock')
  getStock(@Param('productId') productId: string): never {
    throw new NotImplementedException('Contract stub only');
  }
}