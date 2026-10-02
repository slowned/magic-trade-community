"""Binder stock accounting for the first-checkout-wins sale flow.

Adding a card to a cart reserves nothing: the same copy can sit in any number
of carts at once. Stock only moves at checkout, and whoever checks out first
takes it — everyone else gets a 409 and has to drop the item.

Every read/write of seller stock goes through here so the rules stay in one
place: only public binders are for sale, quantities are decremented rather
than rows blindly deleted, and a cancelled order puts the copies back.
"""

from django.db.models import Sum

from binders.models import BinderCard
from carts.models import Cart, CartItemAllocation


class StockUnavailable(Exception):
    """Raised mid-transaction when the seller can't cover the cart.

    Carries the per-card shortfall so the view can render it and so raising it
    rolls the whole checkout back.
    """

    def __init__(self, unavailable):
        self.unavailable = unavailable
        super().__init__('Insufficient binder stock')


def _for_sale(seller, card_ids):
    """Seller rows that are actually on offer: public binders only."""
    return BinderCard.objects.filter(
        binder__user=seller,
        binder__is_public=True,
        card_id__in=card_ids,
    )


def available_quantity(seller, card_id):
    """Copies of one card the seller currently has for sale, across binders."""
    total = _for_sale(seller, [card_id]).aggregate(total=Sum('quantity'))['total']
    return total or 0


def deduct_for_checkout(cart):
    """Take the cart's cards out of the seller's public binders.

    Must be called inside `transaction.atomic()`: the candidate rows are locked
    with `select_for_update` before their quantities are read, so two buyers
    racing for the last copy are serialized and only the first one gets it.

    Raises `StockUnavailable` if any line can't be covered, which rolls back
    the enclosing transaction. Otherwise writes a `CartItemAllocation` per
    binder drawn from, so the sale can be reversed.
    """
    items = list(cart.items.select_related('card').all())
    card_ids = [item.card_id for item in items]

    # One locking read for every card in the cart. `of=('self',)` keeps the
    # lock on the BinderCard rows instead of also taking one on the joined
    # binder, which unrelated checkouts would contend for.
    rows = list(
        _for_sale(cart.seller, card_ids)
        .select_for_update(of=('self',))
        .order_by('binder_id')
    )

    by_card = {}
    for row in rows:
        by_card.setdefault(row.card_id, []).append(row)

    unavailable = []
    for item in items:
        stock = by_card.get(item.card_id, [])
        if sum(row.quantity for row in stock) < item.quantity:
            unavailable.append({
                'id': item.card_id,
                'name': item.card.name,
                'requested': item.quantity,
                'available': sum(row.quantity for row in stock),
            })

    if unavailable:
        raise StockUnavailable(unavailable)

    allocations = []
    emptied = []
    for item in items:
        remaining = item.quantity
        for row in by_card[item.card_id]:
            if remaining == 0:
                break
            taken = min(row.quantity, remaining)
            remaining -= taken
            row.quantity -= taken
            allocations.append(CartItemAllocation(
                item=item,
                binder_id=row.binder_id,
                quantity=taken,
                foil=row.foil,
                etched=row.etched,
                condition=row.condition,
                language=row.language,
            ))
            if row.quantity == 0:
                emptied.append(row.pk)
            else:
                row.save(update_fields=['quantity'])

    if emptied:
        BinderCard.objects.filter(pk__in=emptied).delete()
    CartItemAllocation.objects.bulk_create(allocations)


def restore_from_cancellation(cart):
    """Put a cancelled order's cards back into the binders they came from.

    Idempotent: the allocations are consumed, so a second call is a no-op.
    Binders deleted in the meantime take their allocations with them (the FK
    cascades), and those copies are simply not restored.
    """
    allocations = list(
        CartItemAllocation.objects
        .filter(item__cart=cart)
        .select_related('item')
    )
    if not allocations:
        return

    for alloc in allocations:
        row, created = BinderCard.objects.get_or_create(
            binder_id=alloc.binder_id,
            card_id=alloc.item.card_id,
            condition=alloc.condition,
            language=alloc.language,
            defaults={'quantity': 0, 'foil': alloc.foil, 'etched': alloc.etched},
        )
        row.quantity += alloc.quantity
        row.save(update_fields=['quantity'])

    CartItemAllocation.objects.filter(pk__in=[a.pk for a in allocations]).delete()


def is_binder_sale(cart):
    """Auction carts hold a won card that was never listed, so stock rules skip them."""
    return cart.source == Cart.SOURCE_BINDER
