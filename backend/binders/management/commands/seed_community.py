"""
Populate a dev database with a believable community: users, public binders
full of real cards, and live auctions that already have bidding history.

Cards are sampled from the Card rows already in the DB (loaded by
`load_cards`), so this never touches Scryfall and runs in a second or two.

    docker-compose exec web python manage.py seed_community
    docker-compose exec web python manage.py seed_community --clean
"""
import random
from decimal import Decimal
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from auctions.models import Auction, BidError
from binders.models import Binder, BinderCard, WishlistCard
from cards.models import Card

# Everything this command creates is tagged so --clean can find it again.
DEMO_PASSWORD = 'demo1234'
PLATFORM_USERNAME = 'plataforma'

PEOPLE = [
    ('goblin_lackey', 'Nahuel', 'Ferreyra', 'Rosario', 'Santa Fe'),
    ('mono_azul', 'Camila', 'Duarte', 'La Plata', 'Buenos Aires'),
    ('el_tutor', 'Rodrigo', 'Bianchi', 'Córdoba', 'Córdoba'),
    ('sol_ring_87', 'Micaela', 'Ojeda', 'Tandil', 'Buenos Aires'),
    ('brujo_de_mox', 'Federico', 'Pereyra', 'CABA', 'Buenos Aires'),
    ('lady_geist', 'Ariadna', 'Rossi', 'Mendoza', 'Mendoza'),
    ('tarmo_gordo', 'Sebastián', 'Quiroga', 'Mar del Plata', 'Buenos Aires'),
    ('kikí_jiki', 'Lucía', 'Barrios', 'Neuquén', 'Neuquén'),
    ('draft_infinito', 'Matías', 'Sosa', 'Salta', 'Salta'),
    ('reina_marchita', 'Valentina', 'Acuña', 'Bahía Blanca', 'Buenos Aires'),
]

BINDER_NAMES = [
    'Vendo / Cambio', 'Commander', 'Modern', 'Bulk raras', 'Foils',
    'Legacy staples', 'Pauper', 'Colección personal', 'Duplicados', 'EDH budget',
]

# (card name, starting price ARS, min increment ARS, closes in N days)
AUCTION_PLAN = [
    ('Ragavan, Nimble Pilferer', '150000', '5000', 3),
    ('Force of Will', '80000', '2500', 6),
]


class Command(BaseCommand):
    help = 'Crea usuarios, carpetas con cartas y subastas con pujas para desarrollo.'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=10, help='Cuántos usuarios crear (máx 10).')
        parser.add_argument('--clean', action='store_true', help='Borra lo que creó una corrida anterior y sale.')

    @transaction.atomic
    def handle(self, *args, **options):
        usernames = [p[0] for p in PEOPLE]

        if options['clean']:
            deleted, _ = User.objects.filter(username__in=usernames).delete()
            Auction.objects.filter(title__startswith='[demo]').delete()
            self.stdout.write(self.style.SUCCESS(f'Borrados {deleted} objetos de la comunidad demo.'))
            return

        pool = list(
            Card.objects.exclude(image_uri='')
            .exclude(price_usd=None)
            .order_by('?')
            .values_list('id', flat=True)[:4000]
        )
        if len(pool) < 500:
            raise CommandError(
                'Faltan cartas en la DB para poblar carpetas. Corré `load_cards` primero.'
            )

        rng = random.Random(20260825)  # deterministic runs
        people = PEOPLE[:max(1, min(options['users'], len(PEOPLE)))]

        users = self._create_users(people)
        self._create_binders(users, pool, rng)
        self._create_wishlists(users, pool, rng)
        self._create_auctions(users, rng)

    # ── Users ──

    def _create_users(self, people):
        users = []
        for username, first, last, city, province in people:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'first_name': first, 'last_name': last, 'email': f'{username}@example.com'},
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            # UserProfile is created by a post_save signal; fill in the address.
            profile = user.profile
            profile.city, profile.province = city, province
            profile.phone = f'+54 9 11 {5000 + user.pk % 4000}-{1000 + user.pk % 9000}'
            profile.save()
            users.append(user)

        self.stdout.write(self.style.SUCCESS(f'{len(users)} usuarios (password: {DEMO_PASSWORD})'))
        return users

    # ── Binders ──

    def _create_binders(self, users, pool, rng):
        total_cards = 0
        total_binders = 0

        for user in users:
            names = rng.sample(BINDER_NAMES, rng.randint(2, 3))
            for index, name in enumerate(names):
                binder, _ = Binder.objects.get_or_create(
                    user=user, name=name,
                    # One private binder each, so the public/private split is visible.
                    defaults={'is_public': index < len(names) - 1 or rng.random() > 0.35},
                )
                existing = set(binder.bindercard_set.values_list('card_id', flat=True))
                wanted = rng.randint(35, 90)
                picks = [cid for cid in rng.sample(pool, wanted) if cid not in existing]

                BinderCard.objects.bulk_create([
                    BinderCard(
                        binder=binder,
                        card_id=card_id,
                        quantity=rng.choices([1, 2, 3, 4], weights=[70, 18, 8, 4])[0],
                        foil=rng.random() < 0.18,
                        etched=rng.random() < 0.03,
                    )
                    for card_id in picks
                ], ignore_conflicts=True)

                total_cards += len(picks)
                total_binders += 1

        self.stdout.write(self.style.SUCCESS(f'{total_binders} carpetas con {total_cards} cartas'))

    # ── Wishlists ──

    def _create_wishlists(self, users, pool, rng):
        rows = []
        for user in users:
            for card_id in rng.sample(pool, rng.randint(4, 12)):
                rows.append(WishlistCard(user=user, card_id=card_id))
        WishlistCard.objects.bulk_create(rows, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'{len(rows)} cartas en wishlists'))

    # ── Auctions ──

    def _create_auctions(self, users, rng):
        platform, created = User.objects.get_or_create(
            username=PLATFORM_USERNAME,
            defaults={'is_staff': True, 'email': 'plataforma@example.com'},
        )
        if created:
            platform.set_password(DEMO_PASSWORD)
            platform.save()
            self.stdout.write(self.style.SUCCESS(
                f'Usuario staff "{PLATFORM_USERNAME}" creado (password: {DEMO_PASSWORD})'
            ))

        now = timezone.now()
        for card_name, start, increment, closes_in_days in AUCTION_PLAN:
            card = Card.objects.filter(name=card_name).exclude(image_uri='').first()
            if not card:
                self.stdout.write(self.style.WARNING(f'  sin carta "{card_name}" en la DB, salteada'))
                continue

            title = f'[demo] {card.name}'
            Auction.objects.filter(title=title).delete()
            auction = Auction.objects.create(
                card=card, seller=platform, title=title,
                description='Carta en excelente estado, fotos reales a pedido. Envío a todo el país.',
                starting_price=Decimal(start), min_increment=Decimal(increment),
                starts_at=now - timedelta(days=1),
                ends_at=now + timedelta(days=closes_in_days),
                status='live',
            )
            self._simulate_bidding(auction, users, rng)

            auction.refresh_from_db()
            self.stdout.write(self.style.SUCCESS(
                f'  Subasta "{card.name}": {auction.bid_count} pujas, '
                f'va ${auction.current_price} (líder {auction.current_leader.username})'
            ))

    def _simulate_bidding(self, auction, users, rng):
        """
        Walk a handful of bidders up the ladder through the real proxy logic,
        so the history and the hidden ceilings are exactly what a live auction
        would have produced.
        """
        bidders = rng.sample(users, min(5, len(users)))
        ceiling = auction.starting_price

        for bidder in bidders:
            # Each bidder commits somewhere above the current asking price.
            ceiling = ceiling * Decimal(rng.uniform(1.08, 1.35))
            try:
                auction.place_bid(bidder, ceiling.quantize(Decimal('1')))
            except BidError:
                # Someone's ceiling landed under the running minimum — fine,
                # that's a bidder who walked away.
                continue
