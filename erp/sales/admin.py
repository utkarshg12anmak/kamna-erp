from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from .models import PriceList, PriceListItem, PriceListTier, PriceListStatus
from .services import has_conflicts_for_pricelist, sync_pricelist_coverage

class PriceListTierInline(admin.TabularInline):
    model = PriceListTier
    extra = 0
    fields = ('max_qty','min_unit_price','is_open_ended')
    ordering = ('max_qty',)
    verbose_name = 'Pricing Tier'
    verbose_name_plural = 'Pricing Tiers'
    help_text = 'Add tiers in increasing max_qty order. The last tier can be open-ended (is_open_ended=True, max_qty blank).'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by('max_qty')

class PriceListItemInline(admin.StackedInline):
    model = PriceListItem
    extra = 0
    fields = ('item',)
    inlines = (PriceListTierInline,)
    show_change_link = True

@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ('code','name','territory','status','effective_from','effective_till','updated_at')
    list_filter = ('status','territory')
    search_fields = ('code','name')
    inlines = (PriceListItemInline,)
    actions = ['publish_lists','archive_lists']

    def save_model(self, request, obj, form, change):
        if change:
            prev = PriceList.objects.get(pk=obj.pk)
            if prev.status in [PriceListStatus.PUBLISHED, PriceListStatus.ARCHIVED]:
                changed = set(form.changed_data) - {'status'}
                if changed:
                    raise ValidationError('Non-DRAFT price lists are read-only (except status changes)')
        if not change and not obj.created_by:
            obj.created_by = request.user
        obj.updated_by = request.user
        obj.full_clean()
        super().save_model(request, obj, form, change)
        sync_pricelist_coverage(obj.id)

    def publish_lists(self, request, queryset):
        updated = 0
        for pl in queryset:
            if pl.status == PriceListStatus.DRAFT:
                conflicts = has_conflicts_for_pricelist(pl)
                if conflicts:
                    self.message_user(request, f"{pl.code}: conflicts {conflicts[:5]} ...", level=messages.ERROR)
                    continue
                # Validate tier shapes for every item before publish
                for pli in pl.items.all():
                    tiers = list(pli.tiers.order_by('max_qty'))
                    # ensure at most one open-ended and if present, it is last
                    open_ended_count = sum(1 for t in tiers if t.is_open_ended)
                    if open_ended_count > 1:
                        self.message_user(request, f"{pl.code}: Item {pli.item_id} has multiple open-ended tiers.", level=messages.ERROR)
                        break
                    if open_ended_count == 1 and tiers[-1].is_open_ended is False:
                        self.message_user(request, f"{pl.code}: Item {pli.item_id} open-ended tier must be last.", level=messages.ERROR)
                        break
                else:
                    pl.status = PriceListStatus.PUBLISHED
                    pl.save(update_fields=['status','updated_at'])
                    updated += 1
        self.message_user(request, f"Published {updated} price lists.", level=messages.SUCCESS)
    publish_lists.short_description = 'Publish selected DRAFT price lists'

    def archive_lists(self, request, queryset):
        updated = 0
        for pl in queryset:
            if pl.status in [PriceListStatus.DRAFT, PriceListStatus.PUBLISHED]:
                pl.status = PriceListStatus.ARCHIVED
                pl.save(update_fields=['status','updated_at'])
                updated += 1
        self.message_user(request, f"Archived {updated} price lists.", level=messages.WARNING)
    archive_lists.short_description = 'Archive selected price lists'

class PriceListTierInlineForItem(admin.TabularInline):
    model = PriceListTier
    extra = 0
    fields = ('max_qty','min_unit_price','is_open_ended')
    ordering = ('max_qty',)

@admin.register(PriceListItem)
class PriceListItemAdmin(admin.ModelAdmin):
    """A dedicated admin entry to manage tiers per (price_list ↔ item).
    This appears as a separate menu item named 'Price Tiers'."""
    list_display = ('price_list','item','tiers_count','price_list_status','territory')
    list_filter = ('price_list__status','price_list__territory')
    search_fields = ('price_list__code','item__sku','item__name')
    inlines = (PriceListTierInlineForItem,)

    def tiers_count(self, obj):
        return obj.tiers.count()

    def price_list_status(self, obj):
        return obj.price_list.status

    def territory(self, obj):
        return obj.price_list.territory

    def save_model(self, request, obj, form, change):
        # normal save
        super().save_model(request, obj, form, change)
        # After any PLI change, trigger conflict scan and coverage sync
        pl = obj.price_list
        conflicts = has_conflicts_for_pricelist(pl)
        if conflicts:
            # revert with error
            raise ValidationError({'item': f'Conflicts with existing price list(s): {conflicts[:5]} ...'})
        sync_pricelist_coverage(pl.id)
