import { Module } from '@nestjs/common';
import { MessagesController } from './messages.controller';
import { MessagesService } from './messages.service';
import { PrismaService } from '../common/prisma.service';
import { ClientsModule } from '../clients/clients.module';
import { TasksModule } from '../tasks/tasks.module';

@Module({
  imports: [ClientsModule, TasksModule],
  controllers: [MessagesController],
  providers: [MessagesService, PrismaService],
})
export class MessagesModule {}
