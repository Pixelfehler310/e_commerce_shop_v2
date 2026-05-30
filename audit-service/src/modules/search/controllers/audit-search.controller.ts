import { Controller, Get, NotImplementedException, Query } from '@nestjs/common';

@Controller('v1/audit/search')
export class AuditSearchController {
  @Get()
  searchSnapshots(@Query() query: Record<string, string>): never {
    throw new NotImplementedException('Contract stub only');
  }
}