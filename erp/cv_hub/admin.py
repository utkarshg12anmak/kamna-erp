from django.contrib import admin
from django.utils.html import format_html
from .models import (CvHubEntry, CvHubGSTRegistration, CvHubAddress, CvHubContact,
                     CvHubState, CvHubCity)

@admin.register(CvHubState)
class CvHubStateAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name', 'code']
    ordering = ['name']

@admin.register(CvHubCity)
class CvHubCityAdmin(admin.ModelAdmin):
    list_display = ['name', 'state', 'state_code']
    list_filter = ['state']
    search_fields = ['name', 'state__name']
    ordering = ['state__name', 'name']
    
    def state_code(self, obj):
        return obj.state.code
    state_code.short_description = 'State Code'

class CvHubGSTRegistrationInline(admin.TabularInline):
    model = CvHubGSTRegistration
    extra = 0
    fields = ['taxpayer_type', 'gstin', 'legal_name_of_business', 'is_primary', 'status']

class CvHubAddressInline(admin.TabularInline):
    model = CvHubAddress
    extra = 0
    fields = ['type', 'line1', 'state', 'city', 'pincode', 'is_default_billing', 'is_default_shipping']

class CvHubContactInline(admin.TabularInline):
    model = CvHubContact
    extra = 0
    fields = ['full_name', 'designation', 'phone', 'email', 'is_primary']

@admin.register(CvHubEntry)
class CvHubEntryAdmin(admin.ModelAdmin):
    list_display = ['legal_name', 'trade_name', 'constitution', 'roles_display', 'commerce_display', 'status', 'updated_at']
    list_filter = ['status', 'constitution', 'is_customer', 'is_supplier', 'is_vendor', 'is_logistics', 'for_sales', 'for_purchase']
    search_fields = ['legal_name', 'trade_name', 'registrations__gstin', 'contacts__phone']
    ordering = ['legal_name']
    inlines = [CvHubGSTRegistrationInline, CvHubAddressInline, CvHubContactInline]
    actions = ['mark_as_active', 'mark_as_inactive']
    
    def roles_display(self, obj):
        roles = []
        if obj.is_customer: roles.append('Customer')
        if obj.is_supplier: roles.append('Supplier')
        if obj.is_vendor: roles.append('Vendor')
        if obj.is_logistics: roles.append('Logistics')
        return ', '.join(roles) or '—'
    roles_display.short_description = 'Roles'
    
    def commerce_display(self, obj):
        if obj.for_sales and obj.for_purchase:
            return 'Both'
        elif obj.for_sales:
            return 'Sales'
        elif obj.for_purchase:
            return 'Purchase'
        return '—'
    commerce_display.short_description = 'Commerce'
    
    def mark_as_active(self, request, queryset):
        queryset.update(status='ACTIVE')
    mark_as_active.short_description = 'Mark selected entries as Active'
    
    def mark_as_inactive(self, request, queryset):
        queryset.update(status='INACTIVE')
    mark_as_inactive.short_description = 'Mark selected entries as Inactive'

@admin.register(CvHubGSTRegistration)
class CvHubGSTRegistrationAdmin(admin.ModelAdmin):
    list_display = ['gstin', 'entry', 'taxpayer_type', 'legal_name_of_business', 'is_primary', 'gstin_status']
    list_filter = ['taxpayer_type', 'gstin_status', 'is_primary']
    search_fields = ['gstin', 'legal_name_of_business', 'entry__legal_name']
    ordering = ['entry__legal_name']
    actions = ['mark_as_primary']
    
    def mark_as_primary(self, request, queryset):
        for reg in queryset:
            reg.is_primary = True
            reg.save()  # This will trigger the signal to clear other primaries
    mark_as_primary.short_description = 'Mark as Primary Registration'

@admin.register(CvHubAddress)
class CvHubAddressAdmin(admin.ModelAdmin):
    list_display = ['entry', 'type', 'line1', 'city', 'state', 'pincode', 'is_default_billing', 'is_default_shipping']
    list_filter = ['type', 'state', 'is_default_billing', 'is_default_shipping']
    search_fields = ['entry__legal_name', 'line1', 'city__name', 'pincode']
    ordering = ['entry__legal_name']
    actions = ['set_default_billing', 'set_default_shipping']
    
    def set_default_billing(self, request, queryset):
        for addr in queryset:
            addr.is_default_billing = True
            addr.save()  # This will trigger the signal to clear other defaults
    set_default_billing.short_description = 'Set as Default Billing'
    
    def set_default_shipping(self, request, queryset):
        for addr in queryset:
            addr.is_default_shipping = True
            addr.save()  # This will trigger the signal to clear other defaults
    set_default_shipping.short_description = 'Set as Default Shipping'

@admin.register(CvHubContact)
class CvHubContactAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'entry', 'designation', 'phone', 'email', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['full_name', 'phone', 'email', 'entry__legal_name']
    ordering = ['entry__legal_name', 'full_name']
