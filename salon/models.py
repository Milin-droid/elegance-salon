
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError


class Service(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    # Estimated time required to complete this service
    duration_minutes = models.PositiveIntegerField(default=30)

    def __str__(self):
        return self.name


class Stylist(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Appointment(models.Model):

    SOURCE_CHOICES = [
        ("online", "Online Booking"),
        ("walk_in", "Walk-in"),
    ]

    STATUS_CHOICES = [
        ("booked", "Booked"),
        ("waiting", "Waiting"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    # Online customers have accounts.
    # Walk-in customers may not have accounts.
    customer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments"
    )

    # Used for walk-ins without a customer account
    walk_in_name = models.CharField(max_length=100, blank=True)
    walk_in_phone = models.CharField(max_length=20, blank=True)

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="appointments"
    )

    # Nullable initially to preserve existing appointments.
    # New booking logic will require a stylist.
    stylist = models.ForeignKey(
        Stylist,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="appointments"
    )

    appointment_date = models.DateField()
    appointment_time = models.TimeField()

    source = models.CharField(
        max_length=10,
        choices=SOURCE_CHOICES,
        default="online"
    )

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="booked"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def end_time(self):
        start = datetime.combine(
            self.appointment_date,
            self.appointment_time
        )
        end = start + timedelta(
            minutes=self.service.duration_minutes
        )
        return end.time()
    
    def clean(self):
        super().clean()

        # We can only check conflicts when these fields are available.
        if not all([
            self.stylist_id,
            self.service_id,
            self.appointment_date,
            self.appointment_time,
        ]):
            return

        # Cancelled appointments do not reserve a time slot.
        if self.status == "cancelled":
            return

        proposed_start = datetime.combine(
            self.appointment_date,
            self.appointment_time,
        )
        proposed_end = proposed_start + timedelta(
            minutes=self.service.duration_minutes
        )

        # Find appointments for the same stylist on the same date.
        existing_appointments = Appointment.objects.filter(
            stylist_id=self.stylist_id,
            appointment_date=self.appointment_date,
        ).exclude(status="cancelled")

        # Do not compare an appointment with itself when editing it.
        if self.pk:
            existing_appointments = existing_appointments.exclude(
                pk=self.pk
            )

        for existing in existing_appointments.select_related("service"):
            existing_start = datetime.combine(
                existing.appointment_date,
                existing.appointment_time,
            )
            existing_end = existing_start + timedelta(
                minutes=existing.service.duration_minutes
            )

            # Two appointments conflict if their time intervals overlap.
            if (
                proposed_start < existing_end
                and proposed_end > existing_start
            ):
                raise ValidationError({
                    "appointment_time": (
                        "This stylist is already booked during this time. "
                        "Please choose another time or stylist."
                    )
                })


    def __str__(self):
        customer_name = (
            self.customer.username
            if self.customer
            else self.walk_in_name or "Walk-in customer"
        )

        return (
            f"{customer_name} - "
            f"{self.service.name} - "
            f"{self.appointment_date}"
        )
