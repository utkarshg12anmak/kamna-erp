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
