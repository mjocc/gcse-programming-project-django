import argparse
import csv
from decimal import Decimal

from django.core.management import BaseCommand, CommandError
from django.forms import model_to_dict
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
    help = "import airport or aircraft data from csv files (with no headers)"

    def add_arguments(self, parser):
        parser.add_argument(
            "type",
            choices=("airport", "aircraft"),
            help="the type of object being imported",
            metavar="object",
        )
        parser.add_argument(
            "file",
            type=argparse.FileType("rt"),
            help="path to the csv file",
            metavar="csv-file",
        )
        parser.add_argument(
            "-y",
            "--yes",
            help="answer yes to confirmation automatically",
            action="store_true",
            dest="confirm",
        )

    def handle(self, *args, **options):
        if (
            options["confirm"]
            or input("This will overwrite existing data. Are you sure? [y/n]: ") == "y"
        ):
            if options["type"] == "airport":
                model = Airport
                length = 4
                existing = [airport.code for airport in Airport.objects.all()]
                get_object = get_airport_object
                pk = "code"
                fields = ["name", "distance_from_lpl", "distance_from_boh"]
            elif options["type"] == "aircraft":
                model = Aircraft
                length = 5
                existing = [aircraft.type for aircraft in Aircraft.objects.all()]
                get_object = get_aircraft_object
                pk = "type"
                fields = [
                    "running_cost",
                    "range",
                    "max_standard_class",
                    "min_first_class",
                ]

            reader = list(csv.reader(options["file"]))
            create_objects = []
            update_objects = []
            options["file"].close()

            for row in reader:
                if len(row) != length:
                    raise CommandError("Some lines of the csv file are invalid")
                objects = update_objects if row[0] in existing else create_objects
                objects.append(get_object(row))

            pk_list = [obj.pk for obj in create_objects + update_objects]
            changes = False

            if update_objects:
                existing_model_dicts = [
                    model_to_dict(obj) for obj in model.objects.all()
                ]
                need_updating = []
                for obj in update_objects:
                    if model_to_dict(obj) in existing_model_dicts:
                        continue
                    else:
                        need_updating.append(obj)
                if need_updating:
                    model.objects.bulk_update(need_updating, fields)
                    changes = True

            if create_objects:
                model.objects.bulk_create(create_objects)
                changes = True

            to_delete = model.objects.exclude(pk__in=pk_list)
            if to_delete:
                to_delete.delete()
                changes = True

            if changes:
                self.stdout.write(self.style.SUCCESS("Data imported successfully"))
            else:
                self.stdout.write(
                    "No changes made - existing database data matches that of the file"
                )
        else:
            self.stdout.write(self.style.ERROR("Import cancelled"))
