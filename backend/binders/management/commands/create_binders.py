from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from binders.models import Binder, BinderCard
from cards.models import Card


class Command(BaseCommand):
    help = 'Create defaults binders'

    def handle(self, *args, **kwargs):
        # Obtener la ruta absoluta del archivo JSON

        cards = Card.objects.all()
        first_ten = cards[0:10]

        user = User.objects.get(username="admin")

        binder = Binder.objects.create(user=user, name="ADMIN BINDER")

        for card in first_ten:
            binder_card, created = BinderCard.objects.get_or_create(
                binder=binder, card=card)
            binder_card.quantity += 1
            binder_card.save()

        self.stdout.write(self.style.SUCCESS('created binder created'))
