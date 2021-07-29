from django.forms import ModelForm, formset_factory

from .models import FlightPlan


class FlightPlanForm(ModelForm):
    class Meta:
        model = FlightPlan
        fields = ["save_name"]


FlightPlanFormSet = formset_factory(FlightPlanForm, extra=2)
