import { Body, Controller, Get, Post } from '@nestjs/common';
import { InboundMessageDto } from './dto';
import { MessagesService } from './messages.service';

@Controller('messages')
export class MessagesController {
  constructor(private readonly messagesService: MessagesService) {}

  @Post('inbound')
  inbound(@Body() dto: InboundMessageDto) {
    return this.messagesService.processInbound(dto.channel, dto.senderId, dto.content, dto.metadata);
  }

  @Get()
  list() {
    return this.messagesService.list();
  }
}
