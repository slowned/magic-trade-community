from django.core.management.base import BaseCommand

from auctions.models import settle_due_auctions


class Command(BaseCommand):
    help = (
        'Abre las subastas programadas que ya arrancaron y cierra las vencidas, '
        'creando el carrito del ganador. Pensado para correr por cron cada pocos minutos; '
        'las lecturas de la API hacen lo mismo, así que es una red de seguridad.'
    )

    def handle(self, *args, **options):
        opened, closed = settle_due_auctions()
        self.stdout.write(self.style.SUCCESS(f'Subastas abiertas: {opened} — cerradas: {closed}'))
