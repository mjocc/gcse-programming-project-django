from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.detail import SingleObjectMixin
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
        fp = FlightPlan.objects.get(pk=request.session["current_fp"])
        complete = fp.complete()
    except (FlightPlan.DoesNotExist, KeyError):
        complete = False
    return {"complete": complete}


class IndexView(TemplateView):
    template_name = "profit_calculator/misc/index.html"


class UserLoginView(LoginView):
    template_name = "profit_calculator/auth/login.html"
    error_message = "Username/password combination is invalid. Please try again."

    def form_invalid(self, form):
        messages.error(self.request, self.error_message)
        return super().form_invalid(form)


class UserLogoutView(LogoutView):
    success_message = "Logged out successfully."

    def get_next_page(self):
        messages.success(self.request, self.success_message)
        return super().get_next_page()


class UserSignupView(CreateView):
    model = User
    form_class = UserCreationForm
    template_name = "profit_calculator/auth/signup.html"
    success_url = reverse_lazy("profit_calculator:login")


class FlightPlanView(ListView):
    template_name = "profit_calculator/misc/flightplan_list.html"

    def get_queryset(self):
        return FlightPlan.objects.filter(user=self.request.user)


class AirportView(SuccessMessageMixin, CreateView):
    model = AirportPlan
    fields = ["uk_airport", "foreign_airport"]
    template_name = "profit_calculator/forms/airportplan_form.html"
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
    template_name = "profit_calculator/forms/aircraftplan_form.html"
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
    template_name = "profit_calculator/forms/pricingplan_form.html"
    success_url = reverse_lazy("profit_calculator:pricing_details")
    success_message = "Pricing information submitted successfully."
    error_message = "The submitted pricing information was invalid. Please try again."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # FIXME
        messages.error(self.request, "test", "top")
        context["disable"] = True
        messages.error(self.request, "test", "top")
        context["disable"] = True
        messages.error(self.request, "test", "top")
        context["disable"] = True
        return context

    def form_invalid(self, form):
        messages.error(self.request, self.error_message)
        return super().form_invalid(form)


class ProfitView(DetailView):
    fields = ["airport_plan", "aircraft_plan", "pricing_plan"]
    success_url = reverse_lazy("profit_calculator:profit_information")

    def get_object(self, **kwargs):
        return FlightPlan.objects.get(pk=self.request.session["current_fp"])


class ClearView(View):
    def get(self, request):
        return render(request, "profit_calculator/misc/clear.html")
