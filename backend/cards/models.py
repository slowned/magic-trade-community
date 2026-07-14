from django.db import models


class Card(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    binders = models.ManyToManyField('binders.Binder', through='binders.BinderCard', blank=True)
    name = models.CharField(max_length=255, db_index=True)
    set_name = models.CharField(max_length=255)
    set_code = models.CharField(max_length=10, blank=True, default='')
    color_identity = models.CharField(max_length=255)
    type_line = models.CharField(max_length=255, blank=True, default='')

    uri = models.CharField(max_length=512)
    scryfall_uri = models.CharField(max_length=512)
    image_uri = models.URLField(max_length=512, blank=True, default='')

    price_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    price_usd_foil = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    price_usd_etched = models.DecimalField(max_digits=12, decimal_places=2, null=True)

    # 16-char hex string produced by imagehash.phash(); empty until compute_card_hashes runs
    phash = models.CharField(max_length=16, blank=True, default='')

    class Meta:
        # Keeps pointing at the original table from when this model lived in
        # `binders` — no data migration needed, this is purely a code move.
        db_table = 'binders_card'

    def __str__(self):
        return self.name
