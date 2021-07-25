from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView
from django.views.generic.edit import CreateView

from .models import (
    Aircraft,
    AircraftPlan,
    Airport,
    AirportPlan,
    FlightPlan,
    PricingPlan,
)


def context_processor(request):
    try:
        # FIXME must use currently selected FlightPlan object
        #  (foreign key on User model)
        fp = FlightPlan.objects.get()
        complete = fp.complete()
    except FlightPlan.DoesNotExist:
        complete = False
    return {"complete": complete}


class IndexView(View):
    def get(self, request):
        return render(request, "profit_calculator/index.html")


class AirportView(SuccessMessageMixin, CreateView):
    model = AirportPlan
    fields = ["uk_airport", "foreign_airport"]
    success_url = reverse_lazy("profit_calculator:airport_details")
    success_message = "Airport information submitted successfully."
    error_message = "The submitted airport information was invalid. Please try again."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["airports"] = Airport.objects.all()
        return context

    def form_invalid(self, form):
        messages.error(self.request, self.error_message)
        return super().form_invalid(form)


class AircraftView(SuccessMessageMixin, CreateView):
    model = AircraftPlan
    fields = ["aircraft", "num_first_class"]
    success_url = reverse_lazy("profit_calculator:aircraft_details")
    success_message = "Aircraft information submitted successfully."
    error_message = "The submitted aircraft information was invalid. Please try again."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["aircrafts"] = Aircraft.objects.all()
        context["aircraft_values"] = {
            aircraft.pk: [aircraft.max_standard_class, aircraft.min_first_class]
            for aircraft in Aircraft.objects.all()
        }
        return context

    def form_invalid(self, form):
        messages.error(self.request, self.error_message)
        return super().form_invalid(form)


class PricingView(SuccessMessageMixin, CreateView):
    model = PricingPlan
    fields = ["standard_class_price", "first_class_price"]
    success_url = reverse_lazy("profit_calculator:pricing_details")
    success_message = "Pricing information submitted successfully."
    error_message = "The submitted pricing information was invalid. Please try again."

    def form_invalid(self, form):
        messages.error(self.request, self.error_message)
        return super().form_invalid(form)


class ProfitView(DetailView):
    model = FlightPlan
    fields = ["airport_plan", "aircraft_plan", "pricing_plan"]
    success_url = reverse_lazy("profit_calculator:profit_information")


class ClearView(View):
    def get(self, request):
        return render(request, "profit_calculator/clear.html")
