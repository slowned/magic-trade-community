"""
Management command: seed_data

Creates demo users and binders with real MTG cards fetched from Scryfall.
Each user gets two binders (one public, one private) with thematically
grouped cards so that the app has varied data to browse and test with.

Usage
-----
    python manage.py seed_data              # create users/binders (idempotent)
    python manage.py seed_data --reset      # delete seed users first, then recreate

Credentials
-----------
All seed users share the password  "password123"
    usuario1  — Red Burn / Aggro
    usuario2  — Blue Control
    usuario3  — Green Ramp
    usuario4  — Black Reanimator
    usuario5  — White Weenie
"""
import time

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from binders.models import Binder, BinderCard
from cards.models import Card
from mtg_trade_community.scryfall import CardNotFound, Scryfall, ScryfallRequestError

PASSWORD = 'password123'

# ---------------------------------------------------------------------------
# User definitions
# ---------------------------------------------------------------------------

USERS = [
    {'username': 'usuario1', 'password': PASSWORD, 'email': 'usuario1@mtg.com'},
    {'username': 'usuario2', 'password': PASSWORD, 'email': 'usuario2@mtg.com'},
    {'username': 'usuario3', 'password': PASSWORD, 'email': 'usuario3@mtg.com'},
    {'username': 'usuario4', 'password': PASSWORD, 'email': 'usuario4@mtg.com'},
    {'username': 'usuario5', 'password': PASSWORD, 'email': 'usuario5@mtg.com'},
]

# ---------------------------------------------------------------------------
# Card lists per user
# Each entry is (binder_name, is_public, card_name_list)
# ---------------------------------------------------------------------------

USER_BINDERS = [
    # usuario1 — Red Burn / Aggro
    [
        ('Red Burn', True, [
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
        ]),
        ('Reserva Burn', False, [
            'Lava Spike',
            'Shard Volley',
            'Fiery Islet',
            'Sunbaked Canyon',
        ]),
    ],
    # usuario2 — Blue Control
    [
        ('Blue Control', True, [
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
        ]),
        ('Legacy Staples', True, [
            'Force of Negation',
            'Daze',
            'Spell Pierce',
            'Archmage\'s Charm',
        ]),
    ],
    # usuario3 — Green Ramp
    [
        ('Green Ramp', True, [
            'Primeval Titan',
            'Cultivate',
            'Kodama\'s Reach',
            'Llanowar Elves',
            'Birds of Paradise',
            'Utopia Sprawl',
            'Arbor Elf',
            'Karn Liberated',
            'Ugin, the Spirit Dragon',
            'Valakut, the Molten Pinnacle',
        ]),
        ('Eldrazi', True, [
            'Emrakul, the Aeons Torn',
            'Ulamog, the Infinite Gyre',
            'Kozilek, Butcher of Truth',
        ]),
    ],
    # usuario4 — Black Reanimator
    [
        ('Black Reanimator', True, [
            'Entomb',
            'Reanimate',
            'Animate Dead',
            'Griselbrand',
            'Demonic Tutor',
            'Thoughtseize',
            'Dark Ritual',
            'Cabal Ritual',
            'Exhume',
            'Unmask',
        ]),
        ('Discard Package', True, [
            'Inquisition of Kozilek',
            'Duress',
            'Hymn to Tourach',
            'Raven\'s Crime',
        ]),
    ],
    # usuario5 — White Weenie
    [
        ('White Weenie', True, [
            'Thalia, Guardian of Thraben',
            'Flickerwisp',
            'Mirran Crusader',
            'Mother of Runes',
            'Leonin Arbiter',
            'Aether Vial',
            'Cavern of Souls',
            'Wasteland',
            'Swords to Plowshares',
            'Path to Exile',
        ]),
        ('Equipment', True, [
            'Sword of Fire and Ice',
            'Sword of Feast and Famine',
            'Umezawa\'s Jitte',
        ]),
    ],
]


class Command(BaseCommand):
    """Create demo users and binders with real MTG cards for local development."""

    help = 'Seed the database with demo users, binders, and Scryfall-sourced cards.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing seed users and their data before recreating.',
        )

    def handle(self, *args, **options):
        if options['reset']:
            usernames = [u['username'] for u in USERS]
            deleted, _ = User.objects.filter(username__in=usernames).delete()
            self.stdout.write(f'Deleted {deleted} seed users and their related data.')

        sf = Scryfall()

        for user_data, binder_defs in zip(USERS, USER_BINDERS):
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={'email': user_data['email']},
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f"Creado usuario '{user.username}' (pass: {user_data['password']})"
                ))
            else:
                self.stdout.write(f"Usuario '{user.username}' ya existe, actualizando binders.")

            for binder_name, is_public, card_names in binder_defs:
                binder, _ = Binder.objects.get_or_create(
                    user=user,
                    name=binder_name,
                    defaults={'is_public': is_public},
                )
                self.stdout.write(f"  Binder: '{binder_name}' (público={is_public})")

                for card_name in card_names:
                    card = Card.objects.filter(name__iexact=card_name).first()

                    if not card:
                        self.stdout.write(f'    Descargando "{card_name}" de Scryfall...')
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
                                },
                            )
                            time.sleep(0.1)
                        except CardNotFound:
                            self.stdout.write(self.style.WARNING(f'    No encontrada: "{card_name}"'))
                            continue
                        except ScryfallRequestError as e:
                            self.stdout.write(self.style.WARNING(f'    Error Scryfall "{card_name}": {e}'))
                            continue

                    binder_card, bc_created = BinderCard.objects.get_or_create(
                        binder=binder,
                        card=card,
                        defaults={'quantity': 4},
                    )
                    action = 'agregada' if bc_created else 'ya existe'
                    self.stdout.write(f'      + {card.name} ({card.set_code.upper()}) [{action}]')

        self.stdout.write(self.style.SUCCESS(
            f'\nSeed completo. Usuarios: {", ".join(u["username"] for u in USERS)} — contraseña: {PASSWORD}'
        ))
