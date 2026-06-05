import requests
import time

HEADERS = {'User-Agent': 'MTGTradeCommunity/1.0', 'Accept': 'application/json'}
BASE_URL = 'https://api.scryfall.com'


class CardNotFound(Exception):
    pass


class ScryfallRequestError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f'ScryfallRequestError: {self.message}'


def _get_image_uri(card_data):
    """Return the normal-size image URI, handling double-faced cards."""
    if card_data.get('image_uris'):
        return card_data['image_uris'].get('normal', '')
    faces = card_data.get('card_faces', [])
    if faces and faces[0].get('image_uris'):
        return faces[0]['image_uris'].get('normal', '')
    return ''


class Scryfall:

    def fetch_card_by_name(self, name):
        """
        Fetch a single card by name using the /cards/named endpoint.
        Returns a dict with all fields needed to create a Card model instance.
        Raises CardNotFound if the card doesn't exist.
        """
        url = f'{BASE_URL}/cards/named'
        response = requests.get(url, params={'fuzzy': name}, headers=HEADERS)

        if response.status_code == 404:
            raise CardNotFound(f'Card not found: {name}')
        if not response.ok:
            raise ScryfallRequestError(f'fetch_card_by_name({name}): {response.status_code}')

        data = response.json()
        data['image_uri'] = _get_image_uri(data)
        return data

    def fetch_card_by_id(self, scryfall_id):
        """Fetch a specific card printing by its Scryfall UUID."""
        response = requests.get(f'{BASE_URL}/cards/{scryfall_id}', headers=HEADERS)
        if response.status_code == 404:
            raise CardNotFound(f'Card not found: {scryfall_id}')
        if not response.ok:
            raise ScryfallRequestError(f'fetch_card_by_id({scryfall_id}): {response.status_code}')
        data = response.json()
        data['image_uri'] = _get_image_uri(data)
        return data

    def get_bulk_data_url(self, bulk_type='oracle_cards'):
        """Return the download URL for a Scryfall bulk data file."""
        response = requests.get(f'{BASE_URL}/bulk-data', headers=HEADERS)
        if not response.ok:
            raise ScryfallRequestError(f'get_bulk_data_url: {response.status_code}')
        manifest = response.json()
        for entry in manifest['data']:
            if entry['type'] == bulk_type:
                return entry['download_uri'], entry['name']
        raise ScryfallRequestError(f'Bulk data type "{bulk_type}" not found')

    def iter_bulk_cards(self, bulk_type='oracle_cards'):
        """
        Yield all card dicts from a Scryfall bulk data file.
        Adds 'image_uri' key to each card.
        """
        download_url, _ = self.get_bulk_data_url(bulk_type)
        response = requests.get(download_url, headers=HEADERS, stream=True)
        if not response.ok:
            raise ScryfallRequestError(f'iter_bulk_cards download: {response.status_code}')

        import json
        for card in json.loads(response.content):
            card['image_uri'] = _get_image_uri(card)
            yield card

    def get_all_cards_by_set(self, set_code):
        """Yield all card dicts for a given set code."""
        url = f'{BASE_URL}/cards/search?q=set:{set_code}'

        while url:
            response = requests.get(url, headers=HEADERS)
            if not response.ok:
                raise ScryfallRequestError(f'get_all_cards_by_set({set_code}): {response.status_code}')
            data = response.json()
            for card in data['data']:
                card['image_uri'] = _get_image_uri(card)
                yield card
            url = data.get('next_page') if data.get('has_more') else None
            if url:
                time.sleep(0.1)

    def get_all_sets(self):
        response = requests.get(f'{BASE_URL}/sets/', headers=HEADERS)
        if response.ok:
            return response.json()
        raise ScryfallRequestError(f'get_all_sets: {response.status_code}')
