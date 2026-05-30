import { Body, Controller, Get, NotImplementedException, Param, Post } from '@nestjs/common';

@Controller('v1/billing/charges')
export class BillingChargesController {
  @Post()
  createCharge(@Body() request: unknown): never {
    throw new NotImplementedException('Contract stub only');
  }

  @Get(':correlationId')
  getChargeStatus(@Param('correlationId') correlationId: string): never {
    throw new NotImplementedException('Contract stub only');
  }
}