from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from .models import WorkOrder

def home(request):
    return HttpResponse("Hello from workorders")

def activity_log(request, wo_id):
    work_order = get_object_or_404(WorkOrder, pk=wo_id)
    logs = work_order.activities.all().order_by("-timestamp")

    return render(request, "workorders/activity_log.html", {
        "work_order": work_order,
        "logs": logs
    })