import { Body, Controller, NotImplementedException, Post } from '@nestjs/common';

@Controller('v1/warehouse/simulation')
export class WarehouseSimulationController {
  @Post('failure-mode')
  setFailureMode(@Body() request: unknown): never {
    throw new NotImplementedException('Contract stub only');
  }
}