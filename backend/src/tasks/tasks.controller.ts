import { Body, Controller, Get, Post } from '@nestjs/common';
import { CreateTaskDto } from './dto';
import { TasksService } from './tasks.service';

@Controller('tasks')
export class TasksController {
  constructor(private readonly tasksService: TasksService) {}

  @Post()
  create(@Body() dto: CreateTaskDto) {
    return this.tasksService.create(dto);
  }

  @Get()
  board() {
    return this.tasksService.board();
  }
}
