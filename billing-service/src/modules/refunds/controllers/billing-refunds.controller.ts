import { Body, Controller, NotImplementedException, Post } from '@nestjs/common';

@Controller('v1/billing/refunds')
export class BillingRefundsController {
  @Post()
  createRefund(@Body() request: unknown): never {
    throw new NotImplementedException('Contract stub only');
  }
}