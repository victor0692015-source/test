import { Injectable } from '@nestjs/common';
import { PrismaService } from '../common/prisma.service';
import { CreateTaskDto } from './dto';

@Injectable()
export class TasksService {
  constructor(private prisma: PrismaService) {}

  create(dto: CreateTaskDto) {
    return this.prisma.task.create({
      data: {
        clientId: dto.clientId,
        title: dto.title,
        description: dto.description,
        status: dto.status,
        priority: dto.priority,
        deadline: dto.deadline ? new Date(dto.deadline) : undefined,
        assignedUserId: dto.assignedUserId,
        parentTaskId: dto.parentTaskId,
      },
    });
  }

  board() {
    return this.prisma.task.findMany({ orderBy: { createdAt: 'desc' } });
  }
}
