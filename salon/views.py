
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .models import Service, Stylist, Appointment
from django.views.decorators.http import require_POST


def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            login(request, form.get_user())
            return redirect("home")
    else:
        form = AuthenticationForm()

    return render(request, "salon/login.html", {"form": form})


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()

    return render(request, "salon/register.html", {"form": form})


def home(request):
    search_query = request.GET.get("q", "")

    services = Service.objects.filter(
        name__icontains=search_query
    )

    return render(
        request,
        "salon/home.html",
        {
            "services": services,
            "search_query": search_query,
        },
    )


def service_detail(request, service_id):
    service = get_object_or_404(Service, id=service_id)

    return render(
        request,
        "salon/service_detail.html",
        {"service": service},
    )


def appointment_end(appointment):
    start = datetime.combine(
        appointment.appointment_date,
        appointment.appointment_time,
    )

    return start + timedelta(
        minutes=appointment.service.duration_minutes
    )


def stylist_has_conflict(stylist, appointment_date, start_time, duration):
    proposed_start = datetime.combine(
        appointment_date,
        start_time,
    )
    proposed_end = proposed_start + timedelta(minutes=duration)

    appointments = Appointment.objects.filter(
        stylist=stylist,
        appointment_date=appointment_date,
    ).exclude(status="cancelled").select_related("service")

    for existing in appointments:
        existing_start = datetime.combine(
            existing.appointment_date,
            existing.appointment_time,
        )
        existing_end = appointment_end(existing)

        # Two appointments conflict when their time intervals overlap.
        if (
            proposed_start < existing_end
            and proposed_end > existing_start
        ):
            return True

    return False


@login_required
def book_appointment(request):
    services = Service.objects.all()
    stylists = Stylist.objects.filter(is_active=True)

    if request.method == "POST":
        service_id = request.POST.get("service")
        stylist_id = request.POST.get("stylist")
        date_text = request.POST.get("appointment_date")
        time_text = request.POST.get("appointment_time")

        service = get_object_or_404(Service, id=service_id)
        stylist = get_object_or_404(
            Stylist,
            id=stylist_id,
            is_active=True,
        )

        try:
            appointment_date = date.fromisoformat(date_text)
            appointment_time = datetime.strptime(
                time_text,
                "%H:%M",
            ).time()
        except (TypeError, ValueError):
            messages.error(
                request,
                "Please enter a valid appointment date and time.",
            )
            return redirect("book_appointment")

        today = timezone.localdate()

        if appointment_date < today:
            messages.error(
                request,
                "You cannot book an appointment in the past.",
            )
            return redirect("book_appointment")

        if (
            appointment_date == today
            and appointment_time <= timezone.localtime().time().replace(
                second=0, microsecond=0
            )
        ):
            messages.error(
                request,
                "Please choose a future appointment time.",
            )
            return redirect("book_appointment")

        # Check and save together to reduce the chance of a clash.
        with transaction.atomic():
            if stylist_has_conflict(
                stylist,
                appointment_date,
                appointment_time,
                service.duration_minutes,
            ):
                messages.error(
                    request,
                    "That stylist is already booked during this time. "
                    "Please choose another time or stylist.",
                )
                return redirect("book_appointment")

            Appointment.objects.create(
                customer=request.user,
                service=service,
                stylist=stylist,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                source="online",
                status="booked",
            )

        messages.success(
            request,
            "Your appointment has been booked successfully!",
        )
        return redirect("home")

    return render(
        request,
        "salon/book_appointment.html",
        {
            "services": services,
            "stylists": stylists,
            "today": timezone.localdate().isoformat(),
        },
    )


@login_required
def my_appointments(request):
    appointments = Appointment.objects.filter(
        customer=request.user
    ).select_related(
        "service", "stylist"
    ).order_by(
        "-appointment_date", "-appointment_time"
    )

    return render(
        request,
        "salon/my_appointments.html",
        {"appointments": appointments},
    )


@login_required
@require_POST
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        customer=request.user,
    )

    if appointment.status == "cancelled":
        messages.info(
            request,
            "This appointment is already cancelled."
        )

    elif appointment.status != "booked":
        messages.error(
            request,
            "Only booked appointments can be cancelled."
        )

    else:
        appointment.status = "cancelled"
        appointment.save(update_fields=["status"])

        messages.success(
            request,
            "Appointment cancelled successfully."
        )

    return redirect("my_appointments")


def user_logout(request):
    logout(request)
    return redirect("home")
