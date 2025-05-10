from django.core.management.base import BaseCommand

from binders.models import Card
from mtg_trade_community.scryfall import Scryfall, ScryfallRequestError


class Command(BaseCommand):
    help = 'Populate database from scryfall API'

    def handle(self, *args, **kwargs):
        sf = Scryfall()

        try:
            all_mtg_sets = sf.get_all_sets()['data']
            # TODO: filtrar sets sin tokens ?
        except ScryfallRequestError as e:
            print(e)
            self.stdout.write(self.style.ERROR('Error trying to fetch all mtg sets'))
            return

        for mtg_set in all_mtg_sets:
            try:
                cards = sf.get_all_cards_by_set(mtg_set['code'])
            except ScryfallRequestError as e:
                print(e)
                continue

            print(mtg_set)

            if not cards['has_more']:  # TODO: iterar sobre todas las paginas del set....
                for card_data in cards['data']:

                    print(card_data['name'])
                    card, created = Card.objects.update_or_create(
                        id=card_data['id'],
                        defaults={
                            'name': card_data['name'],
                            'set_name': card_data['set_name'],
                            'color_identity': ','.join(card_data['color_identity']),  # Convierte la lista a cadena
                            'uri': card_data['uri'],
                            'scryfall_uri': card_data['scryfall_uri'],
                            'image_uri': card_data['image_uris']['normal'] if card_data.get('image_uris') else ''
                        }
                    )
            self.stdout.write(self.style.SUCCESS(f'Set "{mtg_set}" created successfully'))

        self.stdout.write(self.style.SUCCESS('Data loaded successfully'))
