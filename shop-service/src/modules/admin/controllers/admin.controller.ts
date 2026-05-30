import { Body, Controller, Get, NotImplementedException, Param, Post, Query } from '@nestjs/common';

@Controller('v1/admin')
export class AdminController {
  @Get('orders')
  listAdminOrders(@Query() query: Record<string, string>): never {
    throw new NotImplementedException('Contract stub only');
  }

  @Get('orders/:correlationId/timeline')
  getOrderTimeline(@Param('correlationId') correlationId: string): never {
    throw new NotImplementedException('Contract stub only');
  }

  @Get('audit/stream')
  streamAudit(@Query() query: Record<string, string>): never {
    throw new NotImplementedException('Contract stub only');
  }

  @Post('simulation/:scenario')
  runSimulationScenario(@Param('scenario') scenario: string, @Body() request: unknown): never {
    throw new NotImplementedException('Contract stub only');
  }
}