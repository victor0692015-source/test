import { CallHandler, ExecutionContext, Injectable, NestInterceptor } from '@nestjs/common';
import { tap } from 'rxjs/operators';
import { PrismaService } from '../prisma.service';

@Injectable()
export class AuditInterceptor implements NestInterceptor {
  constructor(private prisma: PrismaService) {}

  intercept(context: ExecutionContext, next: CallHandler) {
    const req = context.switchToHttp().getRequest();
    return next.handle().pipe(
      tap(async () => {
        await this.prisma.auditLog.create({
          data: {
            userId: req.user?.sub,
            action: `${req.method} ${req.url}`,
            entity: 'http_request',
            changes: { body: req.body },
          },
        });
      }),
    );
  }
}
