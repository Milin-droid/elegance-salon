
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path(
        "services/<int:service_id>/",
        views.service_detail,
        name="service_detail",
    ),
    path("register/", views.register, name="register"),

    path("login/", views.user_login, name="login"),
    
    path("book/", views.book_appointment, name="book_appointment"),

    path("my-appointments/", views.my_appointments, name="my_appointments"),
    path("logout/", views.user_logout, name="logout"),
    path(
    "appointments/<int:appointment_id>/cancel/",
    views.cancel_appointment,
    name="cancel_appointment",
),
]

