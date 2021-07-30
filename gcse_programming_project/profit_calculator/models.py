from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Airport(models.Model):
    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    distance_from_lpl = models.PositiveSmallIntegerField()
    distance_from_boh = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.name


class Aircraft(models.Model):
    type = models.CharField(max_length=30, unique=True)
    running_cost = models.DecimalField(
        "running cost (£/seat/100km)", max_digits=7, decimal_places=2
    )
    range = models.PositiveSmallIntegerField("range (km)")
    max_standard_class = models.PositiveSmallIntegerField(
        help_text="Max number of seats if all of them are standard class."
    )
    min_first_class = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.type


class AirportPlan(models.Model):
    uk_airport = models.CharField(
        "UK airport",
        max_length=3,
        choices=[
            ("LPL", "Liverpool John Lennon Airport"),
            ("BOH", "Bournemouth International Airport"),
        ],
        default="",
    )
    foreign_airport = models.ForeignKey(Airport, on_delete=models.PROTECT, null=True)
    distance = models.PositiveSmallIntegerField(
        "distance between airports (km)", null=True, blank=True
    )

    def details_exist(self):
        return self.uk_airport != "" and self.foreign_airport != ""

    def save(self, *args, **kwargs):
        initial_creation = kwargs.pop("initial_creation", False)
        if self.details_exist():
            if self.uk_airport == "LPL":
                self.distance = self.foreign_airport.distance_from_lpl
            elif self.uk_airport == "BOH":
                self.distance = self.foreign_airport.distance_from_boh
        super().save(*args, **kwargs)
        if not initial_creation:
            self.flightplan.pricing_plan.update()


class AircraftPlan(models.Model):
    aircraft = models.ForeignKey(Aircraft, on_delete=models.PROTECT, null=True)
    num_first_class = models.PositiveSmallIntegerField(
        "Number of first class seats", null=True
    )
    num_standard_class = models.PositiveSmallIntegerField(
        "Number of standard class seats", null=True, blank=True
    )

    def details_exist(self):
        return self.aircraft is not None and self.num_first_class is not None

    def in_range(self):
        if self.details_exist() and self.flightplan.airport_plan.details_exist():
            return self.aircraft.range > self.flightplan.airport_plan.distance
        else:
            return None

    def clean(self):
        if self.num_first_class / 2 > self.aircraft.max_standard_class:
            raise ValidationError(
                {
                    "num_first_class": "The number of first class seats is too large - "
                    f"there must be less than {self.aircraft.max_standard_class / 2}"
                },
                code="invalid",
            )
        return super().clean()

    def save(self, *args, **kwargs):
        initial_creation = kwargs.pop("initial_creation", False)
        if self.details_exist():
            self.num_standard_class = (
                self.aircraft.max_standard_class - self.num_first_class * 2
            )
        super().save(*args, **kwargs)
        if not initial_creation:
            self.flightplan.pricing_plan.update()


class PricingPlan(models.Model):
    standard_class_price = models.DecimalField(
        max_digits=7, decimal_places=2, null=True
    )
    first_class_price = models.DecimalField(max_digits=7, decimal_places=2, null=True)
    cost_per_seat = models.DecimalField(
        "Running cost per seat", max_digits=10, decimal_places=2, null=True, blank=True
    )
    running_cost = models.DecimalField(
        "Total running cost", max_digits=10, decimal_places=2, null=True, blank=True
    )
    income = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    profit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def details_exist(self):
        return (
            self.standard_class_price is not None and self.first_class_price is not None
        )

    def profitable(self):
        return self.profit > 0

    def update(self, *args, **kwargs):
        if self.flightplan.complete():
            self.cost_per_seat = (
                self.flightplan.aircraft_plan.aircraft.running_cost
                * Decimal(self.flightplan.airport_plan.distance / 100)
            )
            self.running_cost = self.cost_per_seat * (
                self.flightplan.aircraft_plan.num_first_class
                + self.flightplan.aircraft_plan.num_standard_class
            )
            self.income = (
                self.flightplan.aircraft_plan.num_first_class * self.first_class_price
                + self.flightplan.aircraft_plan.num_standard_class
                * self.standard_class_price
            )
            self.profit = self.income - self.running_cost
            super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        initial_creation = kwargs.pop("initial_creation", False)
        super().save(*args, **kwargs)
        if not initial_creation:
            self.update()


def default_airportplan():
    ap = AirportPlan()
    ap.save(initial_creation=True)
    return ap.pk


def default_aircraftplan():
    ap = AircraftPlan()
    ap.save(initial_creation=True)
    return ap.pk


def default_pricingplan():
    pp = PricingPlan()
    pp.save(initial_creation=True)
    return pp.pk


class FlightPlan(models.Model):
    airport_plan = models.OneToOneField(
        AirportPlan,
        default=default_airportplan,
        on_delete=models.SET_DEFAULT,
        blank=True,
        auto_created=True,
    )
    aircraft_plan = models.OneToOneField(
        AircraftPlan,
        default=default_aircraftplan,
        on_delete=models.SET_DEFAULT,
        blank=True,
        auto_created=True,
    )
    pricing_plan = models.OneToOneField(
        PricingPlan,
        default=default_pricingplan,
        on_delete=models.SET_DEFAULT,
        blank=True,
        auto_created=True,
    )
    save_name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField("date created", default=timezone.now)

    def __str__(self):
        return self.save_name

    def complete(self):
        return (
            self.airport_plan.details_exist()
            and self.aircraft_plan.details_exist()
            and self.aircraft_plan.in_range()
            and self.pricing_plan.details_exist()
        )
