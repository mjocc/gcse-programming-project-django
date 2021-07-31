import io

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.forms import model_to_dict
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.detail import SingleObjectMixin
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
    return {"complete": complete, "breakpoint": settings.NAVBAR_BREAKPOINT}


def get_current_flightplan(request):
    return FlightPlan.objects.get(pk=request.session["current_fp"])


def get_user_flightplans(request):
    return FlightPlan.objects.filter(user=request.user).order_by(
        "-created", "save_name"
    )


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


class UserSignupView(SuccessMessageMixin, CreateView):
    model = User
    form_class = UserCreationForm
    template_name = "profit_calculator/auth/signup.html"
    success_url = reverse_lazy("profit_calculator:login")
    success_message = "Account created successfully."


class UserPasswordChangeView(SuccessMessageMixin, PasswordChangeView):
    template_name = "profit_calculator/auth/change_password.html"
    success_url = reverse_lazy("profit_calculator:index")
    success_message = "Password changed successfully."


class FlightPlanView(ListView):
    template_name = "profit_calculator/misc/flightplan_list.html"
    paginate_by = 5

    def get_queryset(self):
        return get_user_flightplans(self.request)

    def post(self, request):
        """Set session cookie with current flightplan."""
        request.session["current_fp"] = int(request.POST["selected-fp"])
        return JsonResponse({"success": True})


class CreateFlightPlan(View):
    success_url = reverse_lazy("profit_calculator:flightplans")

    def post(self, request):
        if len(self.request.POST["save-name"]) > 100:
            return self.form_invalid()
        else:
            return self.form_valid()

    def form_valid(self):
        if FlightPlan.objects.filter(user=self.request.user).count() >= 25:
            messages.error(
                "You already have 25 flightplans. This is the maximum "
                "allowed. Please delete at least one and then try again."
            )
            return redirect("profit_calculator:flightplans")
        else:
            fp = FlightPlan(
                save_name=self.request.POST["save-name"], user=self.request.user
            )
            fp.save()
            messages.success(
                self.request, f'Flight plan "{fp.save_name}" created successfully.'
            )
            return redirect(self.success_url)

    def form_invalid(self):
        messages.error(
            self.request,
            "The entered save name is invalid. "
            "Please try again with a different save name.",
        )
        return redirect("profit_calculator:flightplans")


class UpdateFlightPlan(SingleObjectMixin, View):
    success_url = reverse_lazy("profit_calculator:flightplans")

    def post(self, request):
        self.object = self.get_object()
        if len(self.request.POST["save-name"]) > 100:
            return self.form_invalid()
        else:
            return self.form_valid()

    def form_valid(self):
        self.object.save_name = self.request.POST["save-name"]
        self.object.save()
        messages.success(
            self.request,
            f'Flight plan "{self.object.save_name}" updated successfully.',
        )
        return redirect("profit_calculator:flightplans")

    def form_invalid(self):
        messages.error(
            self.request,
            "The entered save name is invalid. "
            "Please try again with a different save name.",
        )
        return redirect("profit_calculator:flightplans")

    def get_object(self, **kwargs):
        fp = get_object_or_404(FlightPlan, pk=self.request.POST["selected-fp"])
        if fp.user == self.request.user:
            return fp
        else:
            raise PermissionDenied(
                "You do not have permission to edit this flight plan."
            )


class DeleteFlightPlan(SingleObjectMixin, View):
    def post(self, request):
        self.object = self.get_object()
        self.object.delete()
        try:
            del request.session["current_fp"]
        except KeyError:
            pass
        messages.success(request, "Flight plan deleted successfully.")
        return redirect("profit_calculator:flightplans")

    def get_object(self, **kwargs):
        try:
            return get_object_or_404(FlightPlan, pk=self.request.POST["selected-fp"])
        except KeyError:
            raise Http404("Selected flightplan does not exist.")


class AirportView(SuccessMessageMixin, UpdateView):
    model = AirportPlan
    fields = ["uk_airport", "foreign_airport"]
    template_name = "profit_calculator/forms/airportplan_form.html"
    success_url = reverse_lazy("profit_calculator:index")
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
    success_url = reverse_lazy("profit_calculator:index")
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
    success_url = reverse_lazy("profit_calculator:index")
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
                mark_safe(
                    f"No airport data has been submitted. This is needed to "
                    f"calculate the profit. Press <a href='"
                    f"{reverse('profit_calculator:airport_details')}'>here</a> to "
                    f"enter it."
                ),
                "top",
            )
            disable = True
        if not fp.aircraft_plan.details_exist():
            messages.error(
                self.request,
                mark_safe(
                    f"No aircraft data has been submitted. This is needed to "
                    f"calculate the profit. Press <a href='"
                    f"{reverse('profit_calculator:aircraft_details')}'>here</a> to "
                    f"enter it."
                ),
                "top",
            )
            disable = True
        if not fp.aircraft_plan.in_range() and not disable:
            messages.error(
                self.request,
                mark_safe(
                    f"This route is longer than the range of the aircraft selected. "
                    f"Please change the aircraft <a href='"
                    f"{reverse('profit_calculator:aircraft_details')}'>here</a> or "
                    f"change the route <a href='"
                    f"{reverse('profit_calculator:airport_details')}'>here</a>."
                ),
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

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.complete():
            messages.error(
                request,
                "You must enter all the required data before accessing the profit "
                "summary.",
            )
            return redirect("profit_calculator:index")
        else:
            return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profitable"] = self.object.pricing_plan.profitable()
        return context

    def get_object(self, **kwargs):
        return get_current_flightplan(self.request)


class ExportView(ListView):
    template_name = "profit_calculator/misc/export.html"

    def get_queryset(self):
        return get_user_flightplans(self.request)

    def post(self, request):
        self.object_list = self.get_queryset()
        filetype = request.POST["filetype"]
        if filetype in ["json", "xml", "yaml"]:
            data = serializers.serialize(filetype, self.object_list)
            file = io.BytesIO(data.encode())
            if filetype == "json":
                content_type = "application/json"
            elif filetype == "xml":
                content_type = "application/xml"
            elif filetype == "yaml":
                content_type = "application/yaml"
            return FileResponse(
                file,
                as_attachment=True,
                filename=f"flightplan.{filetype}",
                content_type=content_type,
            )
        else:
            messages.error("Invalid filetype.")
            return redirect("profit_calculator/misc/export.html")
