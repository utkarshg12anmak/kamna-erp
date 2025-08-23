from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from .models import PriceListItem
from .services import resolve_min_unit_price_for_qty

@staff_member_required
def preview_price(request, pli_id):
    try:
        qty = int(request.GET.get('qty', '0'))
    except ValueError:
        return HttpResponseBadRequest('qty must be integer')
    pli = get_object_or_404(PriceListItem, pk=pli_id)
    tier, price = resolve_min_unit_price_for_qty(pli, qty)
    return JsonResponse({
        'qty': qty,
        'tier': {
            'max_qty': (tier.max_qty if tier else None),
            'is_open_ended': (tier.is_open_ended if tier else None),
            'min_unit_price': (str(tier.min_unit_price) if tier else None)
        },
        'min_unit_price': (str(price) if price is not None else None)
    })
