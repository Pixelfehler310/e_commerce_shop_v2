import { Body, Controller, Delete, NotImplementedException, Param, Post } from '@nestjs/common';

@Controller('v1/warehouse/reservations')
export class WarehouseReservationsController {
  @Post()
  createReservation(@Body() request: unknown): never {
    throw new NotImplementedException('Contract stub only');
  }

  @Delete(':correlationId')
  cancelReservation(@Param('correlationId') correlationId: string): never {
    throw new NotImplementedException('Contract stub only');
  }
}