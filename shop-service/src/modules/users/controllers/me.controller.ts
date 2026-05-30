import { Controller, Get, NotImplementedException } from '@nestjs/common';

@Controller('v1/me')
export class MeController {
  @Get()
  getCurrentUser(): never {
    throw new NotImplementedException('Contract stub only');
  }
}