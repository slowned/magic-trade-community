import time

from django.core.management.base import BaseCommand

from cards.models import Card
from mtg_trade_community.scryfall import Scryfall, ScryfallRequestError


class Command(BaseCommand):
    help = (
        'Load cards from Scryfall bulk data (oracle_cards or default_cards). '
        'Use --sets to load specific sets only (faster for testing).'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--bulk-type',
            default='oracle_cards',
            choices=['oracle_cards', 'default_cards'],
            help='Which Scryfall bulk data set to download (default: oracle_cards)',
        )
        parser.add_argument(
            '--sets',
            nargs='+',
            metavar='SET_CODE',
            help='Load only these set codes instead of all bulk data (e.g. --sets m10 ltr)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Stop after importing this many cards (for testing)',
        )

    def handle(self, *args, **options):
        sf = Scryfall()
        limit = options['limit']
        count = 0
        errors = 0

        if options['sets']:
            cards_iter = self._iter_sets(sf, options['sets'])
        else:
            self.stdout.write(f'Downloading Scryfall bulk data ({options["bulk_type"]})...')
            try:
                cards_iter = sf.iter_bulk_cards(options['bulk_type'])
            except ScryfallRequestError as e:
                self.stdout.write(self.style.ERROR(str(e)))
                return

        for card_data in cards_iter:
            if limit and count >= limit:
                break

            # Skip non-English and tokens
            if card_data.get('lang', 'en') != 'en':
                continue
            if card_data.get('set_type') in ('token', 'memorabilia'):
                continue

            try:
                Card.objects.update_or_create(
                    id=card_data['id'],
                    defaults={
                        'name': card_data['name'],
                        'set_name': card_data.get('set_name', ''),
                        'set_code': card_data.get('set', ''),
                        'color_identity': ','.join(card_data.get('color_identity', [])),
                        'type_line': card_data.get('type_line', ''),
                        'uri': card_data.get('uri', ''),
                        'scryfall_uri': card_data.get('scryfall_uri', ''),
                        'image_uri': card_data.get('image_uri', ''),
                        'price_usd': card_data.get('prices', {}).get('usd') or None,
                        'price_usd_foil': card_data.get('prices', {}).get('usd_foil') or None,
                        'price_usd_etched': card_data.get('prices', {}).get('usd_etched') or None,
                    }
                )
                count += 1
                if count % 500 == 0:
                    self.stdout.write(f'  {count} cards imported...')
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.WARNING(f'  Skipped {card_data.get("name", "?")} — {e}'))

        self.stdout.write(self.style.SUCCESS(
            f'Done. Imported {count} cards. Errors: {errors}.'
        ))

    def _iter_sets(self, sf, set_codes):
        for code in set_codes:
            self.stdout.write(f'Loading set {code.upper()}...')
            try:
                yield from sf.get_all_cards_by_set(code)
                time.sleep(0.1)
            except ScryfallRequestError as e:
                self.stdout.write(self.style.WARNING(str(e)))
