import { Body, Controller, Get, NotImplementedException, Param, Patch, Post, Query } from '@nestjs/common';

@Controller('v1/products')
export class ProductsController {
  @Get()
  listProducts(@Query() query: Record<string, string>): never {
    throw new NotImplementedException('Contract stub only');
  }

  @Get(':productId')
  getProduct(@Param('productId') productId: string): never {
    throw new NotImplementedException('Contract stub only');
  }

  @Post()
  createProduct(@Body() request: unknown): never {
    throw new NotImplementedException('Contract stub only');
  }

  @Patch(':productId')
  updateProduct(@Param('productId') productId: string, @Body() request: unknown): never {
    throw new NotImplementedException('Contract stub only');
  }
}