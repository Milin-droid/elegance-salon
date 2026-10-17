
from django.contrib import admin
from .models import Service, Stylist, Appointment


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "duration_minutes")
    search_fields = ("name",)


@admin.register(Stylist)
class StylistAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "customer",
        "walk_in_name",
        "service",
        "stylist",
        "appointment_date",
        "appointment_time",
        "source",
        "status",
        "created_at",
    )

    list_filter = (
        "source",
        "status",
        "appointment_date",
        "service",
        "stylist",
    )

    search_fields = (
        "customer__username",
        "walk_in_name",
        "walk_in_phone",
        "service__name",
        "stylist__name",
    )
