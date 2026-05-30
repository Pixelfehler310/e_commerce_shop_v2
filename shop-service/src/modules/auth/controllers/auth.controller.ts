import { Body, Controller, NotImplementedException, Post } from '@nestjs/common';

@Controller('v1/auth')
export class AuthController {
  @Post('register')
  register(@Body() request: unknown): never {
    throw new NotImplementedException('Contract stub only');
  }

  @Post('login')
  login(@Body() request: unknown): never {
    throw new NotImplementedException('Contract stub only');
  }
}