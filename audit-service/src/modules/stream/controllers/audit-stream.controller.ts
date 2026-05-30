import { Controller, MessageEvent, NotImplementedException, Query, Sse } from '@nestjs/common';
import { Observable } from 'rxjs';

@Controller('v1/audit')
export class AuditStreamController {
  @Sse('stream')
  streamSnapshots(@Query() query: Record<string, string>): Observable<MessageEvent> {
    throw new NotImplementedException('Contract stub only');
  }
}