import { Controller, NotImplementedException } from '@nestjs/common';
import { EventPattern, Payload } from '@nestjs/microservices';

@Controller()
export class AuditEventsController {
  @EventPattern('audit.domain-events')
  handleDomainEvent(@Payload() event: unknown): never {
    throw new NotImplementedException('Contract stub only');
  }
}