from .models import Location, LocationType, VirtualSubtype, WarehouseStatus


def ensure_location_empty(location_id: int) -> bool:
    """Stub for inventory check. Return True for now.
    TODO: Integrate with stock ledger once inventory module is ready.
    """
    return True


def create_standard_virtual_bins(warehouse):
    subtypes = [
        VirtualSubtype.RECEIVE,
        VirtualSubtype.DISPATCH,
        VirtualSubtype.RETURN,
        VirtualSubtype.QC,
        VirtualSubtype.HOLD,
        VirtualSubtype.DAMAGE,
        VirtualSubtype.LOST,
        VirtualSubtype.EXCESS,
        VirtualSubtype.LOST_PENDING,
        VirtualSubtype.EXCESS_PENDING,
        VirtualSubtype.DAMAGE_PENDING,
    ]
    created = 0
    for st in subtypes:
        obj, was_created = Location.objects.get_or_create(
            warehouse=warehouse,
            type=LocationType.VIRTUAL,
            subtype=st,
            defaults={
                "display_name": st.replace("_", " ").title(),
                "system_managed": True,
                "status": WarehouseStatus.ACTIVE,
            },
        )
        if was_created:
            created += 1
    return created
