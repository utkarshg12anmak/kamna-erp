from .models import Territory, TerritoryMember, TerritoryCoverage, Pincode

def rebuild_territory_coverage(territory_id: int):
    t = Territory.objects.get(pk=territory_id)
    pins = set()
    members = TerritoryMember.objects.filter(territory=t).select_related('state','city','pincode')
    for m in members:
        if m.state_id:
            pins.update(Pincode.objects.filter(state_id=m.state_id, is_active=True).values_list('id', flat=True))
        elif m.city_id:
            pins.update(Pincode.objects.filter(city_id=m.city_id, is_active=True).values_list('id', flat=True))
        elif m.pincode_id and m.pincode.is_active:
            pins.add(m.pincode_id)
    TerritoryCoverage.objects.filter(territory=t).delete()
    TerritoryCoverage.objects.bulk_create([TerritoryCoverage(territory=t, pincode_id=pid) for pid in pins], batch_size=1000, ignore_conflicts=True)
