import { Module } from '@nestjs/common';
import { IntegrationsController } from './integrations.controller';
import { MessagesModule } from '../messages/messages.module';

@Module({
  imports: [MessagesModule],
  controllers: [IntegrationsController],
})
export class IntegrationsModule {}
