import { Body, Controller, NotImplementedException, Post } from '@nestjs/common';

@Controller('v1/audit/snapshots')
export class AuditSnapshotsController {
  @Post()
  appendSnapshot(@Body() request: unknown): never {
    throw new NotImplementedException('Contract stub only');
  }
}