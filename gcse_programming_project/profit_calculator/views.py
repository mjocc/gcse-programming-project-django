from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView

from .models import (
    Aircraft,
    AircraftPlan,
    Airport,
    AirportPlan,
    FlightPlan,
    PricingPlan,
)


def context_processor(request):
    if "current_fp" in request.session:
        try:
            fp = get_current_flightplan(request)
            complete = fp.complete()
        except FlightPlan.DoesNotExist:
            complete = False
    else:
        complete = False
    return {"complete": complete}


def get_current_flightplan(request):
    return FlightPlan.objects.get(pk=request.session["current_fp"])


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

    def post(self, request):
        request.session["current_fp"] = int(request.POST["selected-fp"])
        return JsonResponse({"success": True})


class AirportView(SuccessMessageMixin, UpdateView):
    model = AirportPlan
    fields = ["uk_airport", "foreign_airport"]
    template_name = "profit_calculator/forms/airportplan_form.html"
    success_url = reverse_lazy("profit_calculator:airport_details")
    success_message = "Airport information submitted successfully."
    error_message = "The submitted airport information was invalid. Please try again."

    def get_object(self, **kwargs):
        fp = get_current_flightplan(self.request)
        return fp.airport_plan

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["airports"] = Airport.objects.all()
        return context

    def form_invalid(self, form):
        messages.error(self.request, self.error_message)
        return super().form_invalid(form)


class AircraftView(SuccessMessageMixin, UpdateView):
    model = AircraftPlan
    fields = ["aircraft", "num_first_class"]
    template_name = "profit_calculator/forms/aircraftplan_form.html"
    success_url = reverse_lazy("profit_calculator:aircraft_details")
    success_message = "Aircraft information submitted successfully."
    error_message = "The submitted aircraft information was invalid. Please try again."

    def get_object(self, **kwargs):
        fp = get_current_flightplan(self.request)
        return fp.aircraft_plan

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


class PricingView(SuccessMessageMixin, UpdateView):
    model = PricingPlan
    fields = ["standard_class_price", "first_class_price"]
    template_name = "profit_calculator/forms/pricingplan_form.html"
    success_url = reverse_lazy("profit_calculator:pricing_details")
    success_message = "Pricing information submitted successfully."
    error_message = "The submitted pricing information was invalid. Please try again."

    def get_object(self, **kwargs):
        fp = get_current_flightplan(self.request)
        return fp.pricing_plan

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fp = get_current_flightplan(self.request)
        disable = False
        if not fp.airport_plan.details_exist():
            messages.error(
                self.request,
                f"No airport data has been submitted. This is needed to calculate the "
                f"profit. Press <a href='"
                f"{reverse_lazy('profit_calculator:airport_details')}'>here</a> to "
                f"enter it.",
                "top",
            )
            disable = True
        if not fp.aircraft_plan.details_exist():
            messages.error(
                self.request,
                f"No aircraft data has been submitted. This is needed to calculate the "
                f"profit. Press <a href='"
                f"{reverse_lazy('profit_calculator:aircraft_details')}'>here</a> to "
                f"enter it.",
                "top",
            )
            disable = True
        if not fp.aircraft_plan.in_range() and not disable:
            messages.error(
                self.request,
                f"This route is longer than the range of the aircraft selected. Please "
                f"change the aircraft <a href='"
                f"{reverse_lazy('profit_calculator:aircraft_details')}'>here</a> or "
                f"change the route <a href='"
                f"{reverse_lazy('profit_calculator:airport_details')}'>here</a>.",
                "top",
            )
            disable = True
        context["disable"] = disable
        return context

    def form_invalid(self, form):
        messages.error(self.request, self.error_message)
        return super().form_invalid(form)


class ProfitView(DetailView):
    model = FlightPlan
    fields = ["airport_plan", "aircraft_plan", "pricing_plan"]
    template_name = "profit_calculator/misc/flightplan_detail.html"
    success_url = reverse_lazy("profit_calculator:profit_information")

    def get_object(self, **kwargs):
        return get_current_flightplan(self.request)


class ClearView(TemplateView):
    template_name = "profit_calculator/misc/clear.html"
