import { Body, Controller, Get, Headers, NotImplementedException, Param, Post, Query } from '@nestjs/common';

@Controller('v1/orders')
export class OrdersController {
  @Post()
  createOrder(
    @Headers('x-idempotency-key') idempotencyKey: string | undefined,
    @Headers('x-correlation-id') correlationId: string | undefined,
    @Body() request: unknown
  ): never {
    throw new NotImplementedException('Contract stub only');
  }

  @Get()
  listOrders(@Query() query: Record<string, string>): never {
    throw new NotImplementedException('Contract stub only');
  }

  @Get(':correlationId')
  getOrder(@Param('correlationId') correlationId: string): never {
    throw new NotImplementedException('Contract stub only');
  }
}