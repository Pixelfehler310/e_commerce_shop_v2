import { Controller, NotImplementedException } from '@nestjs/common';
import { EventPattern, Payload } from '@nestjs/microservices';

@Controller()
export class InvoiceEventsController {
  @EventPattern('PaymentSucceeded')
  handlePaymentSucceeded(@Payload() event: unknown): never {
    throw new NotImplementedException('Contract stub only');
  }
}