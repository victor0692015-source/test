import { Module } from '@nestjs/common';
import { TasksController } from './tasks.controller';
import { TasksService } from './tasks.service';
import { SmartTaskService } from './smart-task.service';
import { PrismaService } from '../common/prisma.service';

@Module({
  controllers: [TasksController],
  providers: [TasksService, SmartTaskService, PrismaService],
  exports: [TasksService, SmartTaskService],
})
export class TasksModule {}
