import { Body, Controller, NotImplementedException, Post } from '@nestjs/common';

@Controller('v1/warehouse/bookings')
export class WarehouseBookingsController {
  @Post()
  bookReservedStock(@Body() request: unknown): never {
    throw new NotImplementedException('Contract stub only');
  }
}