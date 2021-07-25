from django.db import models
from django.utils import timezone


class Airport(models.Model):
    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    distance_from_lpl = models.FloatField()
    distance_from_boh = models.FloatField()

    def __str__(self):
        return self.name


class Aircraft(models.Model):
    type = models.CharField(max_length=30, unique=True)
    running_cost = models.DecimalField(
        "running cost (£/seat/100km)", max_digits=7, decimal_places=2
    )
    range = models.FloatField("range (km)")
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
    distance = models.FloatField("distance between airports", null=True)

    def details_exist(self):
        return self.uk_airport != "" and self.foreign_airport != ""

    def save(self, *args, **kwargs):
        if self.uk_airport == "LPL":
            self.distance = self.foreign_airport.distance_from_lpl
        elif self.uk_airport == "BOH":
            self.distance = self.foreign_airport.distance_from_boh
        super().save(*args, **kwargs)
        self.flightplan.pricing_plan.update()


class AircraftPlan(models.Model):
    aircraft = models.ForeignKey(Aircraft, on_delete=models.PROTECT, null=True)
    num_first_class = models.PositiveSmallIntegerField(
        "Number of first class seats", null=True
    )
    num_standard_class = models.PositiveSmallIntegerField(
        "Number of standard class seats", null=True
    )

    def details_exist(self):
        return self.aircraft is not None and self.num_first_class is not None

    def in_range(self):
        if self.details_exist() and self.flightplan.airport_plan.details_exist():
            return self.aircraft.range > self.flightplan.airport_plan.distance
        else:
            return None

    def save(self, *args, **kwargs):
        self.num_standard_class = (
            self.aircraft.max_standard_class - self.num_first_class * 2
        )
        super().save(*args, **kwargs)
        self.flightplan.pricing_plan.update()


class PricingPlan(models.Model):
    standard_class_price = models.DecimalField(
        max_digits=7, decimal_places=2, null=True
    )
    first_class_price = models.DecimalField(max_digits=7, decimal_places=2, null=True)
    cost_per_seat = models.FloatField("Running cost per seat", null=True)
    running_cost = models.FloatField("Total running cost", null=True)
    income = models.FloatField(null=True)
    profit = models.FloatField(null=True)

    def details_exist(self):
        return (
            self.standard_class_price is not None and self.first_class_price is not None
        )

    def update(self, *args, **kwargs):
        if self.flightplan.complete():
            self.cost_per_seat = self.flightplan.aircraft_plan.aircraft.running_cost * (
                self.flightplan.airport_plan.distance / 100
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
        super().save(*args, **kwargs)
        self.update()


class FlightPlan(models.Model):
    airport_plan = models.OneToOneField(
        AirportPlan, default=AirportPlan, on_delete=models.SET_DEFAULT
    )
    aircraft_plan = models.OneToOneField(
        AircraftPlan, default=AircraftPlan, on_delete=models.SET_DEFAULT
    )
    pricing_plan = models.OneToOneField(
        PricingPlan, default=PricingPlan, on_delete=models.SET_DEFAULT
    )
    save_name = models.CharField(max_length=100)
    updated = models.DateTimeField("date created/last updated", default=timezone.now)

    def complete(self):
        return (
            self.airport_plan.details_exist()
            and self.airport_plan.details_exist()
            and self.aircraft_plan.in_range()
            and self.pricing_plan.details_exist()
        )
