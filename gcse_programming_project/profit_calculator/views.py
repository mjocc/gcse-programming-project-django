from django.shortcuts import render

# Create your views here.
from django.views import generic


def index(request):
    render(
        request,
        "profit_calculator/index.html",
    )
