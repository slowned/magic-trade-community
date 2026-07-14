"""
Management command: compute_card_hashes

Downloads each card image stored in the Card table and computes a difference
hash (dhash) using only Pillow.  No imagehash, numpy, OpenCV, or scipy
required — fully compatible with Alpine Linux.

The hash is saved to Card.phash so the scanner endpoint can perform fast
Hamming-distance comparisons without hitting Scryfall at query time.

Usage
-----
    python manage.py compute_card_hashes              # cards without a hash
    python manage.py compute_card_hashes --all        # recompute every card
    python manage.py compute_card_hashes --limit 500  # at most N cards
"""
import io
import time

import requests
from django.core.management.base import BaseCommand
from PIL import Image

from cards.models import Card

HEADERS = {'User-Agent': 'MTGTradeCommunity/1.0'}
CARD_SIZE = (200, 280)
HASH_SIZE = 8
DELAY = 0.05


def _dhash(image):
    """
    Compute a 64-bit difference hash from a PIL image.
    Returns a 16-character hex string.  Requires only Pillow.
    """
    thumb = image.resize((HASH_SIZE + 1, HASH_SIZE), Image.LANCZOS).convert('L')
    pixels = list(thumb.getdata())
    bits = []
    for row in range(HASH_SIZE):
        for col in range(HASH_SIZE):
            left = pixels[row * (HASH_SIZE + 1) + col]
            right = pixels[row * (HASH_SIZE + 1) + col + 1]
            bits.append('1' if left < right else '0')
    return f'{int("".join(bits), 2):016x}'


def _hash_from_url(image_url):
    """
    Download *image_url* and return its dhash hex string.
    Returns None on any download or decode failure.
    """
    try:
        response = requests.get(image_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        image = Image.open(io.BytesIO(response.content)).convert('RGB')
        resized = image.resize(CARD_SIZE, Image.LANCZOS)
        return _dhash(resized)
    except Exception:
        return None


class Command(BaseCommand):
    """Download card images from Scryfall and compute difference hashes (dhash)."""

    help = 'Compute dhash for every Card in the DB that has an image_uri.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Recompute hashes even for cards that already have one.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Maximum number of cards to process (useful for testing).',
        )

    def handle(self, *args, **options):
        qs = Card.objects.exclude(image_uri='')
        if not options['all']:
            qs = qs.filter(phash='')
        if options['limit']:
            qs = qs[:options['limit']]

        total = qs.count()
        self.stdout.write(f'Cartas a procesar: {total}')

        ok = skipped = errors = 0

        for i, card in enumerate(qs, start=1):
            prefix = f'[{i}/{total}] {card.name} ({card.set_code.upper()})'

            if not card.image_uri:
                self.stdout.write(self.style.WARNING(f'{prefix} — sin image_uri, omitida'))
                skipped += 1
                continue

            h = _hash_from_url(card.image_uri)
            if h is None:
                self.stdout.write(self.style.ERROR(f'{prefix} — error al descargar'))
                errors += 1
            else:
                card.phash = h
                card.save(update_fields=['phash'])
                self.stdout.write(f'{prefix} → {h}')
                ok += 1

            time.sleep(DELAY)

        self.stdout.write(self.style.SUCCESS(
            f'\nListo. OK: {ok}  Omitidas: {skipped}  Errores: {errors}'
        ))
