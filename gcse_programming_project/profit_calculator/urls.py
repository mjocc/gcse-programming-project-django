from django.urls import path

from . import views

app_name = "profit_calculator"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("signup/", views.UserSignupView.as_view(), name="signup"),
    path("flightplans/", views.FlightPlanView.as_view(), name="flightplans"),
    path("airport/", views.AirportView.as_view(), name="airport_details"),
    path("aircraft/", views.AircraftView.as_view(), name="aircraft_details"),
    path("pricing/", views.PricingView.as_view(), name="pricing_details"),
    path("profit/", views.ProfitView.as_view(), name="profit_information"),
    path("clear/", views.ClearView.as_view(), name="clear_data"),
]
