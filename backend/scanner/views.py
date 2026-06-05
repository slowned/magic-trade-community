"""
Scanner views — identify a Magic: The Gathering card from a camera frame.

Algorithm
---------
1. Client POSTs a base64-encoded JPEG frame captured from the phone camera.
2. The image is opened with Pillow and center-cropped to the card area.
3. A difference hash (dhash) is computed using only Pillow — no imagehash,
   numpy, OpenCV or scipy needed (fully Alpine compatible).
4. The query hash is compared (Hamming distance) against every Card row that
   already has a stored hash.  The row with the smallest distance is returned
   as the match, provided it falls below MAX_DISTANCE.

Why dhash instead of OCR?
--------------------------
A card name like "Dark Ritual" exists in 20+ printings with different artwork
and prices.  OCR reads the name but cannot distinguish printings.  Because
each printing has unique artwork, a visual hash naturally resolves to the
correct edition.
"""
import base64
import io

from PIL import Image
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from binders.models import Card
from binders.serializers import CardSerializer
from mtg_trade_community.authentication import OptionalJWTAuthentication

# Cards whose Hamming distance to the query hash exceeds this threshold are
# rejected.  64 is the maximum possible distance for a 64-bit dhash.
MAX_DISTANCE = 40

CARD_WIDTH = 200
CARD_HEIGHT = 280
HASH_SIZE = 8   # produces a 64-bit hash (8×8 pixel grid)


# ---------------------------------------------------------------------------
# Pure-Pillow dhash implementation
# ---------------------------------------------------------------------------

def _dhash(image):
    """
    Compute a 64-bit difference hash from a PIL image.

    Each bit represents whether the left pixel is brighter than the right
    pixel in an (HASH_SIZE+1) × HASH_SIZE grayscale thumbnail.  The result
    is returned as a 16-character hex string.

    Requires only Pillow — no numpy, scipy, or imagehash.
    """
    thumb = image.resize((HASH_SIZE + 1, HASH_SIZE), Image.LANCZOS).convert('L')
    pixels = list(thumb.getdata())
    bits = []
    for row in range(HASH_SIZE):
        for col in range(HASH_SIZE):
            left = pixels[row * (HASH_SIZE + 1) + col]
            right = pixels[row * (HASH_SIZE + 1) + col + 1]
            bits.append('1' if left < right else '0')
    value = int(''.join(bits), 2)
    return f'{value:016x}'


def _hamming(hex1, hex2):
    """Return the Hamming distance between two 16-char hex hash strings."""
    xor = int(hex1, 16) ^ int(hex2, 16)
    return bin(xor).count('1')


# ---------------------------------------------------------------------------
# Image-processing helpers
# ---------------------------------------------------------------------------

def _center_crop(image):
    """
    Crop the center 60% width / 80% height of the frame.

    When the user points the camera at a card, the card occupies roughly this
    region.  Lightweight alternative to full contour detection.
    """
    w, h = image.size
    return image.crop((int(w * 0.20), int(h * 0.10), int(w * 0.80), int(h * 0.90)))


def _compute_hash(image):
    """Crop, resize to canonical card size, and return the dhash hex string."""
    cropped = _center_crop(image)
    resized = cropped.resize((CARD_WIDTH, CARD_HEIGHT), Image.LANCZOS)
    return _dhash(resized)


def _find_top_cards(query_hash, top_n=3):
    """
    Scan all Card rows with a stored hash and return the top N closest matches.

    Fetches (id, phash) pairs in a single query, computes Hamming distances
    in Python, then fetches the winning Cards in one more query.

    Returns:
        List of (card_id, distance) sorted by distance, filtered by MAX_DISTANCE.
    """
    results = []

    for card_id, stored_hash in Card.objects.exclude(phash='').values_list('id', 'phash'):
        try:
            d = _hamming(query_hash, stored_hash)
        except Exception:
            continue
        if d <= MAX_DISTANCE:
            results.append((card_id, d))

    results.sort(key=lambda x: x[1])
    results = results[:top_n]

    if not results:
        return []

    card_ids = [r[0] for r in results]
    cards_by_id = {c.id: c for c in Card.objects.filter(id__in=card_ids)}
    return [(cards_by_id[cid], dist) for cid, dist in results if cid in cards_by_id]


# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------

class CardIdentifyView(APIView):
    """
    POST /scanner/identify/

    Accepts a base64-encoded JPEG frame and identifies the Magic card using
    a pure-Pillow difference hash comparison against the Card table.

    Request body (JSON)
    -------------------
    { "image": "<base64-encoded JPEG string>" }

    Response (200) — match found
    ----------------------------
    { "card": {...}, "distance": <int 0–64>, "confidence": <float 0–1> }

    Response (200) — no match
    -------------------------
    { "card": null, "message": "No se encontró ninguna carta." }

    Errors: 400 bad image, 401 not authenticated.
    """
    authentication_classes = [OptionalJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Decode the frame, hash it, and return the best DB match."""
        image_b64 = request.data.get('image')
        if not image_b64:
            return Response(
                {'error': 'Falta el campo "image".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            image_bytes = base64.b64decode(image_b64)
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        except Exception:
            return Response(
                {'error': 'Imagen inválida o no se pudo decodificar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        query_hash = _compute_hash(image)
        matches = _find_top_cards(query_hash)

        if not matches:
            return Response({'card': None, 'message': 'No se encontró ninguna carta.'})

        best_card, best_distance = matches[0]
        confidence = round(1 - (best_distance / 64), 2)
        return Response({
            'card': CardSerializer(best_card).data,
            'distance': best_distance,
            'confidence': confidence,
            'candidates': [
                {
                    'card': CardSerializer(c).data,
                    'distance': d,
                    'confidence': round(1 - (d / 64), 2),
                }
                for c, d in matches
            ],
        })
