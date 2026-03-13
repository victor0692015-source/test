import { Channel } from '@prisma/client';
import { Injectable } from '@nestjs/common';
import { PrismaService } from '../common/prisma.service';
import { ClientsService } from '../clients/clients.service';
import { SmartTaskService } from '../tasks/smart-task.service';
import { TasksService } from '../tasks/tasks.service';

@Injectable()
export class MessagesService {
  constructor(
    private prisma: PrismaService,
    private clientsService: ClientsService,
    private smartTaskService: SmartTaskService,
    private tasksService: TasksService,
  ) {}

  async processInbound(channel: Channel, senderId: string, content: string, metadata?: Record<string, unknown>) {
    const client =
      (await this.prisma.client.findFirst({ where: { OR: [{ telegramHandle: senderId }, { whatsappNumber: senderId }, { viberId: senderId }] } })) ||
      (await this.clientsService.create({ name: `Lead ${senderId}`, tags: ['auto-created'], telegramHandle: channel === 'TELEGRAM' ? senderId : undefined, whatsappNumber: channel === 'WHATSAPP' ? senderId : undefined, viberId: channel === 'VIBER' ? senderId : undefined }));

    const message = await this.prisma.message.create({
      data: { clientId: client.id, channel, direction: 'inbound', content, metadata },
    });

    const taskIntent = this.smartTaskService.extractTaskIntent(content);
    if (taskIntent) {
      await this.tasksService.create({
        clientId: client.id,
        title: taskIntent.title,
        deadline: taskIntent.deadline?.toISOString(),
      });
    }

    return message;
  }

  list() {
    return this.prisma.message.findMany({ orderBy: { createdAt: 'desc' }, take: 200 });
  }
}
