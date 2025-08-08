from django.shortcuts import render


def landing_page(request):
    return render(request, "landing_page.html")


def module_hub(request):
    return render(request, "module_hub.html")


def module_catalog(request):
    return render(request, "module_catalog.html")


def module_warehousing(request):
    return render(request, "module_warehousing.html")


def module_manufacturing(request):
    return render(request, "module_manufacturing.html")


def module_sales(request):
    return render(request, "module_sales.html")


def module_finance(request):
    return render(request, "module_finance.html")
