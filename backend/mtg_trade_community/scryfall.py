import gzip
import json
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
        """Return the download URL for a Scryfall bulk data file.

        Scryfall now publishes these as JSON Lines under `jsonl_download_uri`;
        `download_uri` (a single huge JSON array) is kept as a fallback for
        older mirrors.
        """
        response = requests.get(f'{BASE_URL}/bulk-data', headers=HEADERS)
        if not response.ok:
            raise ScryfallRequestError(f'get_bulk_data_url: {response.status_code}')
        manifest = response.json()
        for entry in manifest['data']:
            if entry['type'] == bulk_type:
                url = entry.get('jsonl_download_uri') or entry.get('download_uri')
                if not url:
                    raise ScryfallRequestError(f'Bulk data "{bulk_type}" has no download URL')
                return url, entry['name']
        raise ScryfallRequestError(f'Bulk data type "{bulk_type}" not found')

    def iter_bulk_cards(self, bulk_type='oracle_cards'):
        """
        Yield all card dicts from a Scryfall bulk data file.
        Adds 'image_uri' key to each card.

        Parsed one line at a time, so memory stays flat even for the
        multi-gigabyte exports.
        """
        download_url, _ = self.get_bulk_data_url(bulk_type)
        response = requests.get(download_url, headers=HEADERS, stream=True)
        if not response.ok:
            raise ScryfallRequestError(f'iter_bulk_cards download: {response.status_code}')

        # Scryfall serves the export as a .gz *file*, with no Content-Encoding
        # header, so requests hands it over still compressed.
        response.raw.decode_content = True
        stream = response.raw
        if download_url.endswith('.gz') or response.headers.get('Content-Type') == 'application/gzip':
            stream = gzip.GzipFile(fileobj=response.raw)

        for raw in stream:
            if not raw:
                continue
            line = raw.decode('utf-8') if isinstance(raw, bytes) else raw
            # Tolerate the legacy JSON-array framing as well as plain JSONL.
            line = line.strip().rstrip(',')
            if line in ('[', ']'):
                continue
            try:
                card = json.loads(line)
            except json.JSONDecodeError:
                continue
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

    def fetch_cards_by_ids(self, ids):
        """
        Batch-resolve Scryfall UUIDs via POST /cards/collection.

        Same 75-per-request budget as `fetch_cards_by_names`. Returns
        {id: card_data} for the ones that resolved; the rest are simply absent.
        """
        found = {}
        batch_size = 75

        for i in range(0, len(ids), batch_size):
            batch = ids[i:i + batch_size]
            response = requests.post(
                f'{BASE_URL}/cards/collection',
                json={'identifiers': [{'id': card_id} for card_id in batch]},
                headers=HEADERS,
            )
            if not response.ok:
                raise ScryfallRequestError(f'fetch_cards_by_ids: {response.status_code}')

            for card in response.json().get('data', []):
                card['image_uri'] = _get_image_uri(card)
                found[card['id']] = card

            if i + batch_size < len(ids):
                time.sleep(0.1)

        return found

    def fetch_cards_by_names(self, names):
        """
        Batch-resolve card names via POST /cards/collection (exact match,
        case-insensitive, up to 75 identifiers per request) instead of one
        /cards/named request per card.

        Returns (found, not_found):
          - found: dict of {name.lower(): card_data} for names that matched.
          - not_found: list of the original names that didn't match exactly
            (typos, alternate spellings — callers may want to retry those
            through fetch_card_by_name's fuzzy lookup).
        """
        found = {}
        not_found = []
        batch_size = 75

        for i in range(0, len(names), batch_size):
            batch = names[i:i + batch_size]
            response = requests.post(
                f'{BASE_URL}/cards/collection',
                json={'identifiers': [{'name': name} for name in batch]},
                headers=HEADERS,
            )
            if not response.ok:
                raise ScryfallRequestError(f'fetch_cards_by_names: {response.status_code}')

            data = response.json()
            for card in data.get('data', []):
                card['image_uri'] = _get_image_uri(card)
                found[card['name'].lower()] = card
            for identifier in data.get('not_found', []):
                if 'name' in identifier:
                    not_found.append(identifier['name'])

            if i + batch_size < len(names):
                time.sleep(0.1)

        return found, not_found

    def autocomplete(self, query):
        """Return up to 20 card name suggestions for the given partial query."""
        response = requests.get(
            f'{BASE_URL}/cards/autocomplete',
            params={'q': query},
            headers=HEADERS
        )
        if not response.ok:
            return []
        return response.json().get('data', [])

    def get_all_sets(self):
        response = requests.get(f'{BASE_URL}/sets/', headers=HEADERS)
        if response.ok:
            return response.json()
        raise ScryfallRequestError(f'get_all_sets: {response.status_code}')
