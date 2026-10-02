from django.contrib import admin

from auctions.models import Auction, Bid


class BidInline(admin.TabularInline):
    model = Bid
    extra = 0
    readonly_fields = ('bidder', 'max_amount', 'price_after', 'became_leader', 'created_at')
    can_delete = False


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ('id', 'display_title', 'status', 'current_price', 'bid_count', 'starts_at', 'ends_at', 'winner')
    list_filter = ('status', 'condition', 'foil')
    search_fields = ('title', 'card__name')
    readonly_fields = (
        'current_price', 'current_leader', 'leader_max_amount', 'bid_count',
        'winner', 'winning_amount', 'closed_at', 'cart', 'created_at', 'updated_at',
    )
    inlines = [BidInline]


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('id', 'auction', 'bidder', 'max_amount', 'price_after', 'became_leader', 'created_at')
    search_fields = ('bidder__username', 'auction__card__name')
