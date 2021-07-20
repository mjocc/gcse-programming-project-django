from django.db import models
from django.utils import timezone


class Airport(models.Model):
    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=50)
    distance_from_lpl = models.FloatField()
    distance_from_boh = models.FloatField()

    def __str__(self):
        return self.name


class Aircraft(models.Model):
    type = models.CharField(max_length=30)
    running_cost = models.FloatField("running cost (£/seat/100km)")
    range = models.FloatField("range (km)")
    max_standard_class = models.PositiveSmallIntegerField(
        help_text="Max number of seats if all of them are standard class."
    )
    min_first_class = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.type


class AirportPlan(models.Model):
    uk_airport = models.CharField(
        max_length=3,
        choices=[
            ("LPL", "Liverpool John Lennon Airport"),
            ("BOH", "Bournemouth International Airport"),
        ],
    )
    foreign_airport = models.ForeignKey(Airport, on_delete=models.PROTECT)
    distance = models.FloatField("distance between airports")


class AircraftPlan(models.Model):
    aircraft = models.ForeignKey(Aircraft, on_delete=models.PROTECT)
    num_first_class = models.PositiveSmallIntegerField("Number of first class seats")
    num_standard_class = models.PositiveSmallIntegerField(
        "Number of standard class seats"
    )


class PricingPlan(models.Model):
    standard_class_price = models.DecimalField(max_digits=7, decimal_places=2)
    first_class_price = models.DecimalField(max_digits=7, decimal_places=2)
    cost_per_seat = models.FloatField("Running cost per seat")
    running_cost = models.FloatField("Total running cost")
    income = models.FloatField()
    profit = models.FloatField()


class FlightPlan(models.Model):
    airport_plan = models.OneToOneField(
        AirportPlan, null=True, on_delete=models.SET_NULL
    )
    aircraft_plan = models.OneToOneField(
        AircraftPlan, null=True, on_delete=models.SET_NULL
    )
    pricing_plan = models.OneToOneField(
        PricingPlan, null=True, on_delete=models.SET_NULL
    )
    save_name = models.CharField(max_length=100, default="")
    updated = models.DateTimeField("date created/last updated", default=timezone.now)
