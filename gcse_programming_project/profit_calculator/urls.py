from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    # path("/airport", views.AirportView.as_view(), name="airport_details"),
    # path("/aircraft", views.AircraftView.as_view(), name="aircraft_details"),
    # path("/pricing", views.PricingView.as_view(), name="pricing_details"),
    # path("/profit", views.ProfitView.as_view(), name="profit_information"),
    # path("/clear", views.ClearView.as_view(), name="clear_data"),
]
