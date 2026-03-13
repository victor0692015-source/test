import { Injectable } from '@nestjs/common';
import { CreateClientDto } from './dto';
import { PrismaService } from '../common/prisma.service';
import { EncryptionService } from '../common/crypto/encryption.service';

@Injectable()
export class ClientsService {
  private encryption = new EncryptionService(process.env.FIELD_ENCRYPTION_KEY || 'local-key');

  constructor(private prisma: PrismaService) {}

  create(dto: CreateClientDto) {
    return this.prisma.client.create({
      data: {
        name: dto.name,
        phoneEncrypted: dto.phone ? this.encryption.encrypt(dto.phone) : null,
        emailEncrypted: dto.email ? this.encryption.encrypt(dto.email) : null,
        company: dto.company,
        tags: dto.tags || [],
        notes: dto.notes,
        telegramHandle: dto.telegramHandle,
        whatsappNumber: dto.whatsappNumber,
        viberId: dto.viberId,
      },
    });
  }

  list() {
    return this.prisma.client.findMany({ orderBy: { createdAt: 'desc' } });
  }

  timeline(clientId: string) {
    return this.prisma.timelineEvent.findMany({ where: { clientId }, orderBy: { createdAt: 'desc' } });
  }
}
