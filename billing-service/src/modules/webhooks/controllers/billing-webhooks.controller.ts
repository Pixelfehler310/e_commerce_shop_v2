import { Body, Controller, NotImplementedException, Param, Post } from '@nestjs/common';

@Controller('v1/billing/webhooks')
export class BillingWebhooksController {
  @Post(':provider')
  receiveProviderWebhook(@Param('provider') provider: string, @Body() request: unknown): never {
    throw new NotImplementedException('Contract stub only');
  }
}