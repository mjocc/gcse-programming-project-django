from django.contrib import admin

from .models import (
    Aircraft,
    AircraftPlan,
    Airport,
    AirportPlan,
    FlightPlan,
    PricingPlan,
)

admin.site.site_header = "Flight profitability calculator administration"
admin.site.site_title = "Flight plan administration"


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Name", {"fields": ("code", "name")}),
        ("Location", {"fields": ("distance_from_lpl", "distance_from_boh")}),
    )
    list_display = ("code", "name")
    ordering = ("name",)
    search_fields = ("code", "name")


@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Type", {"fields": ("type",)}),
        ("Pricing", {"fields": ("running_cost",)}),
        (
            "Specification",
            {"fields": ("range", "max_standard_class", "min_first_class")},
        ),
    )
    ordering = ("pk",)
    search_fields = ("type",)


@admin.register(FlightPlan)
class FlightPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "save_name", "created", "user", "complete")
    list_display_links = ("save_name",)
    ordering = ("-created", "save_name")
    search_fields = ("save_name",)
    fields = ("save_name", "user", "created")
