import { Body, Controller, NotImplementedException, Post } from '@nestjs/common';

@Controller('v1/billing/simulation')
export class BillingSimulationController {
  @Post('provider-mode')
  setProviderMode(@Body() request: unknown): never {
    throw new NotImplementedException('Contract stub only');
  }
}