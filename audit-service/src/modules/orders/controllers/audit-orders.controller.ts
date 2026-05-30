import { Controller, Get, NotImplementedException, Param } from '@nestjs/common';

@Controller('v1/audit/orders')
export class AuditOrdersController {
  @Get(':correlationId')
  getOrderHistory(@Param('correlationId') correlationId: string): never {
    throw new NotImplementedException('Contract stub only');
  }
}