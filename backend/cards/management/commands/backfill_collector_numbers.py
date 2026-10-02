"""Fill in `collector_number` for cards imported before the field existed.

Scryfall's bulk file is one download for the whole catalogue, so this is much
cheaper than asking for 34k cards one at a time. Cards already carrying a
number are left alone, which makes the command safe to re-run.
"""
from django.core.management.base import BaseCommand

from cards.models import Card
from mtg_trade_community.scryfall import Scryfall, ScryfallRequestError

BATCH_SIZE = 1000


class Command(BaseCommand):
    help = 'Backfill Card.collector_number from Scryfall bulk data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bulk-type',
            default='oracle_cards',
            choices=['oracle_cards', 'default_cards'],
            help=(
                'Bulk file to read. Defaults to oracle_cards, which is what seeded the '
                'catalogue and is small enough to hold in memory; default_cards covers '
                'every printing but is several GB once parsed.'
            ),
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Also overwrite cards that already have a collector number',
        )

    def handle(self, *args, **options):
        wanted = Card.objects.all() if options['all'] else Card.objects.filter(collector_number='')
        missing = set(wanted.values_list('id', flat=True))

        if not missing:
            self.stdout.write(self.style.SUCCESS('Nothing to backfill.'))
            return

        self.stdout.write(f'{len(missing)} cards without a collector number.')
        self.stdout.write(f'Downloading Scryfall bulk data ({options["bulk_type"]})...')

        try:
            cards_iter = Scryfall().iter_bulk_cards(options['bulk_type'])
        except ScryfallRequestError as exc:
            self.stdout.write(self.style.ERROR(str(exc)))
            return

        pending = []
        updated = 0
        for data in cards_iter:
            if data['id'] not in missing:
                continue
            number = data.get('collector_number', '')
            if not number:
                continue
            pending.append(Card(id=data['id'], collector_number=number))
            if len(pending) >= BATCH_SIZE:
                updated += self._flush(pending)

        updated += self._flush(pending)

        # Printings pulled in one at a time (by id, from a binder or an auction)
        # aren't in the oracle export. There are few enough to ask for directly.
        updated += self._resolve_stragglers()

        self.stdout.write(self.style.SUCCESS(f'Done. Updated {updated} cards.'))
        still_missing = Card.objects.filter(collector_number='').count()
        if still_missing:
            self.stdout.write(self.style.WARNING(
                f'{still_missing} cards still have no number — Scryfall did not resolve them.'
            ))

    def _resolve_stragglers(self):
        leftover = list(Card.objects.filter(collector_number='').values_list('id', flat=True))
        if not leftover:
            return 0

        self.stdout.write(f'Resolving {len(leftover)} stragglers by id...')
        try:
            found = Scryfall().fetch_cards_by_ids(leftover)
        except ScryfallRequestError as exc:
            self.stdout.write(self.style.WARNING(f'  Could not resolve stragglers: {exc}'))
            return 0

        pending = [
            Card(id=card_id, collector_number=data['collector_number'])
            for card_id, data in found.items()
            if data.get('collector_number')
        ]
        return self._flush(pending)

    def _flush(self, pending):
        if not pending:
            return 0
        Card.objects.bulk_update(pending, ['collector_number'])
        count = len(pending)
        pending.clear()
        self.stdout.write(f'  {count} updated...')
        return count
