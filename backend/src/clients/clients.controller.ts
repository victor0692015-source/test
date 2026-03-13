import { Body, Controller, Get, Param, Post } from '@nestjs/common';
import { ClientsService } from './clients.service';
import { CreateClientDto } from './dto';

@Controller('clients')
export class ClientsController {
  constructor(private readonly clientsService: ClientsService) {}

  @Post()
  create(@Body() dto: CreateClientDto) {
    return this.clientsService.create(dto);
  }

  @Get()
  list() {
    return this.clientsService.list();
  }

  @Get(':id/timeline')
  timeline(@Param('id') id: string) {
    return this.clientsService.timeline(id);
  }
}
