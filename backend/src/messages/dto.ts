import { Channel } from '@prisma/client';
import { IsEnum, IsOptional, IsString } from 'class-validator';

export class InboundMessageDto {
  @IsEnum(Channel)
  channel!: Channel;

  @IsString()
  senderId!: string;

  @IsString()
  content!: string;

  @IsOptional()
  metadata?: Record<string, unknown>;
}
