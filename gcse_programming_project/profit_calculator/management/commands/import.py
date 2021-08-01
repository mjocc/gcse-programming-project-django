import argparse
import csv
from decimal import Decimal

from django.core.management import BaseCommand, CommandError
from profit_calculator.models import Aircraft, Airport


def get_airport_object(row):
    return Airport(
        code=row[0],
        name=row[1],
        distance_from_lpl=int(row[2]),
        distance_from_boh=int(row[3]),
    )


def get_aircraft_object(row):
    return Aircraft(
        type=row[0],
        running_cost=Decimal(row[1]),
        range=int(row[2]),
        max_standard_class=int(row[3]),
        min_first_class=int(row[4]),
    )


class Command(BaseCommand):
    help = "import airport or aircraft data from csv files (with no headers)."

    def add_arguments(self, parser):
        parser.add_argument(
            "type",
            choices=("airport", "aircraft"),
            help="the type of object being imported",
        )
        parser.add_argument(
            "file",
            type=argparse.FileType("rt"),
            help="path to the csv file",
        )

    def handle(self, *args, **options):
        if (
            input(
                "This will remove every reference to the selected model. "
                "Are you sure? [y/n]: "
            )
            == "y"
        ):
            if options["type"] == "airport":
                model = Airport
                length = 4
                get_object = get_airport_object
            elif options["type"] == "aircraft":
                model = Aircraft
                length = 5
                get_object = get_aircraft_object
            reader = list(csv.reader(options["file"]))
            objects = []
            options["file"].close()
            for row in reader:
                if len(row) != length:
                    raise CommandError("Some lines of the csv file are invalid")
                objects.append(get_object(row))
            model.objects.all().delete()
            model.objects.bulk_create(objects)
            self.stdout.write(self.style.SUCCESS("Data imported successfully"))
        else:
            self.stdout.write(self.style.ERROR("Import cancelled"))
