from django.contrib import admin
from .models import Part, WorkOrder, RepairStep, Inspection, ActivityLog

admin.site.register(Part)
admin.site.register(WorkOrder)
admin.site.register(RepairStep)
admin.site.register(Inspection)
admin.site.register(ActivityLog)