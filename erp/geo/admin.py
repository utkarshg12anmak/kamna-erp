from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
import csv, io
from .models import State, City, Pincode

class PincodeInline(admin.TabularInline):
    model = Pincode
    extra = 0
    fields = ('code', 'is_active', 'state')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

class CityInline(admin.TabularInline):
    model = City
    extra = 0
    fields = ('name', 'is_active')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    fields = ('code', 'name', 'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by')
    inlines = (CityInline,)
    actions = ['deactivate_states_with_cascade']

    def save_model(self, request, obj, form, change):
        """Automatically set audit fields - these should not be manually editable."""
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def deactivate_states_with_cascade(self, request, queryset):
        updated_states = queryset.update(is_active=False)
        City.objects.filter(state__in=queryset).update(is_active=False)
        Pincode.objects.filter(state__in=queryset).update(is_active=False)
        self.message_user(request, f"Deactivated {updated_states} states and cascaded to related cities and pincodes.", level=messages.WARNING)
    deactivate_states_with_cascade.short_description = 'Deactivate selected states (cascade)'

    # CSV upload admin view
    @method_decorator(csrf_protect)
    def import_csv_view(self, request):
        if request.method == 'POST' and request.FILES.get('file'):
            f = request.FILES['file']
            try:
                data = f.read().decode('utf-8')
            except Exception:
                self.message_user(request, 'Could not read file. Ensure UTF-8 CSV.', level=messages.ERROR)
                return redirect('..')
            reader = csv.DictReader(io.StringIO(data))
            expected = {'STATE','CITY','PINCODE'}
            if set(map(str.upper, reader.fieldnames or [])) != expected:
                self.message_user(request, 'CSV header must be exactly: STATE,CITY,PINCODE', level=messages.ERROR)
                return redirect('..')
            created_s=updated_s=created_c=updated_c=created_p=updated_p=conflict_p=0
            for row in reader:
                sc = (row['STATE'] or '').strip().upper()
                cn = (row['CITY'] or '').strip()
                pc = (row['PINCODE'] or '').strip()
                if not sc or not cn or not pc:
                    continue
                # upsert state
                s, s_new = State.objects.get_or_create(code=sc, defaults={'name': sc, 'is_active': True, 'created_by': request.user, 'updated_by': request.user})
                if s_new:
                    created_s += 1
                else:
                    changed = False
                    if not s.name:
                        s.name = sc; changed = True
                    if changed:
                        s.updated_by = request.user; s.save(); updated_s += 1
                # upsert city
                c, c_new = City.objects.get_or_create(state=s, name=cn, defaults={'is_active': True, 'created_by': request.user, 'updated_by': request.user})
                if c_new:
                    created_c += 1
                else:
                    # no name change here; only active toggle would be manual
                    pass
                # upsert pincode (global unique)
                p = Pincode.objects.filter(code=pc).first()
                if not p:
                    Pincode.objects.create(code=pc, state=s, city=c, is_active=True, created_by=request.user, updated_by=request.user)
                    created_p += 1
                else:
                    if p.state_id != s.id or p.city_id != c.id:
                        conflict_p += 1  # do not move; report conflict
                    else:
                        updated_p += 1  # nothing to change except updated_by
                        p.updated_by = request.user; p.save(update_fields=['updated_by','updated_at'])
            self.message_user(request, f"CSV done: State(created={created_s}, updated={updated_s}), City(created={created_c}), Pincode(created={created_p}, updated={updated_p}, conflicts={conflict_p}).", level=messages.SUCCESS)
            return redirect('..')
        context = {
            **self.admin_site.each_context(request),
            'title': 'Import STATE,CITY,PINCODE CSV',
            'opts': self.model._meta,
        }
        return render(request, 'admin/geo_import_csv.html', context)

    def get_urls(self):
        urls = super().get_urls()
        custom = [path('import-csv/', self.admin_site.admin_view(self.import_csv_view), name='geo_state_import_csv')]
        return custom + urls

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'is_active', 'created_at', 'updated_at')
    list_filter = ('state', 'is_active', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    fields = ('state', 'name', 'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by')
    inlines = (PincodeInline,)
    
    def save_model(self, request, obj, form, change):
        """Automatically set audit fields - these should not be manually editable."""
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Pincode)
class PincodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'city', 'state', 'is_active', 'created_at', 'updated_at')
    list_filter = ('state', 'city', 'is_active', 'created_at')
    search_fields = ('code',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    fields = ('code', 'state', 'city', 'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by')
    autocomplete_fields = ('state', 'city')
    
    def save_model(self, request, obj, form, change):
        """Automatically set audit fields - these should not be manually editable."""
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# Territory Admin
from django import forms
from .models import Territory, TerritoryMember


class TerritoryMemberInlineForm(forms.ModelForm):
    class Meta:
        model = TerritoryMember
        fields = ['state', 'city', 'pincode']
    
    def clean(self):
        cleaned = super().clean()
        # let model.clean() enforce rules
        self.instance.territory = self.instance.territory
        self.instance.state = cleaned.get('state')
        self.instance.city = cleaned.get('city')
        self.instance.pincode = cleaned.get('pincode')
        self.instance.clean()
        return cleaned


class TerritoryMemberInline(admin.TabularInline):
    model = TerritoryMember
    form = TerritoryMemberInlineForm
    extra = 0
    fields = ('state', 'city', 'pincode')
    
    def get_fields(self, request, obj=None):
        if not obj:
            return ('state', 'city', 'pincode')
        return ('state',) if obj.type == 'STATE' else ('city',) if obj.type == 'CITY' else ('pincode',)


@admin.register(Territory)
class TerritoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'type', 'is_active', 'members_count', 'effective_from', 'effective_till', 'updated_at')
    list_filter = ('type', 'is_active', 'created_at')
    search_fields = ('code', 'name')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    fields = ('code', 'name', 'type', 'is_active', 'effective_from', 'effective_till', 'notes', 'created_at', 'updated_at', 'created_by', 'updated_by')
    inlines = (TerritoryMemberInline,)
    actions = ['activate_territories', 'deactivate_territories']

    def save_model(self, request, obj, form, change):
        """Automatically set audit fields and normalize data."""
        from django.db import transaction
        from .models import TerritoryCoverage
        
        # Get previous pincodes before saving
        prev_pins = set()
        if change:
            prev_pins = set(TerritoryCoverage.objects.filter(territory=obj).values_list('pincode_id', flat=True))
        
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        obj.clean()
        
        with transaction.atomic():
            super().save_model(request, obj, form, change)
            
            # After save, check for added pincodes that could cause conflicts
            if change:
                new_pins = set(TerritoryCoverage.objects.filter(territory=obj).values_list('pincode_id', flat=True))
                added = new_pins - prev_pins
                
                if added:
                    # Check if this territory has any PUBLISHED price lists
                    try:
                        from sales.models import PriceList, PriceCoverage, PriceListStatus
                        published_lists = PriceList.objects.filter(territory=obj, status=PriceListStatus.PUBLISHED)
                        
                        if published_lists.exists():
                            # Check for conflicts on added pincodes
                            for pincode_id in added:
                                conflicting = PriceCoverage.objects.filter(
                                    pincode_id=pincode_id,
                                    status__in=[PriceListStatus.DRAFT, PriceListStatus.PUBLISHED]
                                ).exclude(price_list__territory=obj).select_related('price_list')
                                
                                for pc in conflicting:
                                    # Check for overlapping windows
                                    for pl in published_lists:
                                        from sales.services import windows_overlap
                                        if windows_overlap(pl.effective_from, pl.effective_till, pc.effective_from, pc.effective_till):
                                            from django.core.exceptions import ValidationError
                                            raise ValidationError(f'Territory expansion would create pricing conflicts for pincode {pincode_id} with price list {pc.price_list.code}')
                    except ImportError:
                        # Sales app not available yet, skip conflict check
                        pass

    def members_count(self, obj):
        return obj.members.count()
    members_count.short_description = 'Members'

    def activate_territories(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} territories.", level=messages.SUCCESS)
    activate_territories.short_description = 'Activate selected territories'

    def deactivate_territories(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {updated} territories.", level=messages.WARNING)
    deactivate_territories.short_description = 'Deactivate selected territories'

    # ---- Admin CSV import/export for members (per territory type) ----
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('<path:object_id>/import-members/', self.admin_site.admin_view(self.import_members_view), name='geo_territory_import_members'),
            path('<path:object_id>/export-members/', self.admin_site.admin_view(self.export_members_view), name='geo_territory_export_members'),
        ]
        return custom + urls

    def import_members_view(self, request, object_id):
        territory = self.get_object(request, object_id)
        if request.method == 'POST' and request.FILES.get('file'):
            f = request.FILES['file']
            try:
                data = f.read().decode('utf-8')
            except Exception:
                self.message_user(request, 'Upload a UTF-8 CSV file', level=messages.ERROR)
                return redirect('..')
            
            reader = csv.DictReader(io.StringIO(data))
            ttype = territory.type
            expected = {'STATE': {'STATE_CODE'}, 'CITY': {'STATE_CODE', 'CITY_NAME'}, 'PINCODE': {'PINCODE'}}[ttype]
            
            if set(map(str.upper, reader.fieldnames or [])) != expected:
                self.message_user(request, f'CSV header must be exactly: {", ".join(expected)}', level=messages.ERROR)
                return redirect('..')
            
            added = dupes = inactive = unknown = 0
            for row in reader:
                try:
                    if ttype == 'STATE':
                        sc = (row['STATE_CODE'] or '').strip().upper()
                        s = State.objects.filter(code=sc).first()
                        if not s: 
                            unknown += 1
                            continue
                        if not s.is_active: 
                            inactive += 1
                            continue
                        obj, created = TerritoryMember.objects.get_or_create(territory=territory, state=s)
                        if created:
                            added += 1
                        else:
                            dupes += 1
                    elif ttype == 'CITY':
                        sc = (row['STATE_CODE'] or '').strip().upper()
                        cn = (row['CITY_NAME'] or '').strip()
                        s = State.objects.filter(code=sc).first()
                        if not s: 
                            unknown += 1
                            continue
                        c = City.objects.filter(state=s, name=cn).first()
                        if not c: 
                            unknown += 1
                            continue
                        if not (s.is_active and c.is_active): 
                            inactive += 1
                            continue
                        obj, created = TerritoryMember.objects.get_or_create(territory=territory, city=c)
                        if created:
                            added += 1
                        else:
                            dupes += 1
                    else:  # PINCODE
                        pc = (row['PINCODE'] or '').strip()
                        p = Pincode.objects.filter(code=pc).first()
                        if not p: 
                            unknown += 1
                            continue
                        if not p.is_active: 
                            inactive += 1
                            continue
                        obj, created = TerritoryMember.objects.get_or_create(territory=territory, pincode=p)
                        if created:
                            added += 1
                        else:
                            dupes += 1
                except Exception:
                    unknown += 1
            
            self.message_user(request, f'Import complete: added={added}, duplicates={dupes}, inactive={inactive}, unknown={unknown}', level=messages.SUCCESS)
            return redirect('..')
        
        ctx = {
            **self.admin_site.each_context(request), 
            'opts': self.model._meta, 
            'title': f'Import {territory.code} members',
            'territory': territory
        }
        return render(request, 'admin/geo_import_members.html', ctx)

    def export_members_view(self, request, object_id):
        from django.http import HttpResponse
        territory = self.get_object(request, object_id)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={territory.code}_members.csv'
        writer = csv.writer(response)
        
        if territory.type == 'STATE':
            writer.writerow(['STATE_CODE'])
            for m in territory.members.select_related('state'):
                writer.writerow([m.state.code])
        elif territory.type == 'CITY':
            writer.writerow(['STATE_CODE', 'CITY_NAME'])
            for m in territory.members.select_related('city__state'):
                writer.writerow([m.city.state.code, m.city.name])
        else:  # PINCODE
            writer.writerow(['PINCODE'])
            for m in territory.members.select_related('pincode'):
                writer.writerow([m.pincode.code])
        
        return response
