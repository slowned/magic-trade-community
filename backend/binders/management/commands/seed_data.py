"""
Creates demo users and binders with real MTG cards fetched from Scryfall.

Usage:
    python manage.py seed_data
    python manage.py seed_data --reset   # drops existing seed users first
"""
import time

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from binders.models import Binder, BinderCard, Card
from mtg_trade_community.scryfall import CardNotFound, Scryfall, ScryfallRequestError

USERS = [
    {'username': 'usuario1', 'password': '123', 'email': 'usuario1@mtg.com'},
    {'username': 'usuario2', 'password': '123', 'email': 'usuario2@mtg.com'},
]

# Two thematic sets of cards so each user has a distinct binder
CARDS_USER1 = [
    'Lightning Bolt',
    'Goblin Guide',
    'Monastery Swiftspear',
    'Eidolon of the Great Revel',
    'Light Up the Stage',
    'Rift Bolt',
    'Searing Blaze',
    'Skullcrack',
    'Inspiring Vantage',
    'Sacred Foundry',
]

CARDS_USER2 = [
    'Counterspell',
    'Force of Will',
    'Snapcaster Mage',
    'Brainstorm',
    'Ponder',
    'Cryptic Command',
    'Flooded Strand',
    'Scalding Tarn',
    'Jace, the Mind Sculptor',
    'Mystic Sanctuary',
]


class Command(BaseCommand):
    help = 'Create demo users and binders for local development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing seed users and their data before recreating',
        )

    def handle(self, *args, **options):
        if options['reset']:
            for u in USERS:
                User.objects.filter(username=u['username']).delete()
            self.stdout.write('Deleted existing seed users.')

        sf = Scryfall()
        card_lists = [CARDS_USER1, CARDS_USER2]

        for i, user_data in enumerate(USERS):
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={'email': user_data['email']},
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f"Created user '{user.username}' (pass: {user_data['password']})"
                ))
            else:
                self.stdout.write(f"User '{user.username}' already exists, skipping creation.")

            binder_name = f"Binder de {user.username}"
            binder, _ = Binder.objects.get_or_create(
                user=user,
                name=binder_name,
                defaults={'is_public': True},
            )

            for card_name in card_lists[i]:
                card = Card.objects.filter(name__iexact=card_name).first()

                if not card:
                    self.stdout.write(f'  Fetching "{card_name}" from Scryfall...')
                    try:
                        data = sf.fetch_card_by_name(card_name)
                        card, _ = Card.objects.update_or_create(
                            id=data['id'],
                            defaults={
                                'name': data['name'],
                                'set_name': data.get('set_name', ''),
                                'set_code': data.get('set', ''),
                                'color_identity': ','.join(data.get('color_identity', [])),
                                'type_line': data.get('type_line', ''),
                                'uri': data.get('uri', ''),
                                'scryfall_uri': data.get('scryfall_uri', ''),
                                'image_uri': data.get('image_uri', ''),
                                'price_usd': data.get('prices', {}).get('usd') or None,
                                'price_usd_foil': data.get('prices', {}).get('usd_foil') or None,
                                'price_usd_etched': data.get('prices', {}).get('usd_etched') or None,
                            }
                        )
                        time.sleep(0.1)
                    except CardNotFound:
                        self.stdout.write(self.style.WARNING(f'  Not found: "{card_name}"'))
                        continue
                    except ScryfallRequestError as e:
                        self.stdout.write(self.style.WARNING(f'  Scryfall error for "{card_name}": {e}'))
                        continue

                binder_card, created = BinderCard.objects.get_or_create(
                    binder=binder, card=card
                )
                if created:
                    binder_card.quantity = 4
                    binder_card.save()

                self.stdout.write(f'    + {card.name} ({card.set_code.upper()})')

        self.stdout.write(self.style.SUCCESS('\nSeed data created. Users: usuario1/123, usuario2/123'))
