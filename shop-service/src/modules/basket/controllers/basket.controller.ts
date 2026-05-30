import { Body, Controller, Delete, Get, NotImplementedException, Param, Patch, Post } from '@nestjs/common';

@Controller('v1/baskets')
export class BasketController {
  @Get()
  getActiveBasket(): never {
    throw new NotImplementedException('Contract stub only');
  }

  @Post('items')
  addBasketItem(@Body() request: unknown): never {
    throw new NotImplementedException('Contract stub only');
  }

  @Patch('items/:productId')
  updateBasketItem(@Param('productId') productId: string, @Body() request: unknown): never {
    throw new NotImplementedException('Contract stub only');
  }

  @Delete('items/:productId')
  removeBasketItem(@Param('productId') productId: string): never {
    throw new NotImplementedException('Contract stub only');
  }
}