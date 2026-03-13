import { Body, Controller, Post } from '@nestjs/common';
import { MessagesService } from '../messages/messages.service';

@Controller('integrations')
export class IntegrationsController {
  constructor(private readonly messagesService: MessagesService) {}

  @Post('telegram/webhook')
  telegramWebhook(@Body() payload: any) {
    return this.messagesService.processInbound('TELEGRAM', String(payload.message?.from?.id), payload.message?.text || '', payload);
  }

  @Post('whatsapp/webhook')
  whatsappWebhook(@Body() payload: any) {
    const msg = payload?.entry?.[0]?.changes?.[0]?.value?.messages?.[0];
    return this.messagesService.processInbound('WHATSAPP', msg?.from || 'unknown', msg?.text?.body || '', payload);
  }

  @Post('viber/webhook')
  viberWebhook(@Body() payload: any) {
    return this.messagesService.processInbound('VIBER', payload.sender?.id || 'unknown', payload.message?.text || '', payload);
  }
}
