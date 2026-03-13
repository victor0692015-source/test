import { Injectable } from '@nestjs/common';

@Injectable()
export class SmartTaskService {
  extractTaskIntent(message: string): { title: string; deadline?: Date } | null {
    const pattern = /create task:\s*(.+)/i;
    const match = message.match(pattern);
    if (!match) return null;

    const title = match[1].trim();
    const tomorrow1400 = /tomorrow at 14:00/i.test(title);
    const deadline = tomorrow1400
      ? new Date(new Date().setDate(new Date().getDate() + 1))
      : undefined;

    if (deadline) deadline.setHours(14, 0, 0, 0);
    return { title, deadline };
  }
}
