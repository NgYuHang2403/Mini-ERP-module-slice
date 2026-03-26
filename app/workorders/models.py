from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class Part(models.Model):
    serial_number = models.CharField(max_length=100, unique=True)
    part_number = models.CharField(max_length=100)
    description = models.TextField()

    def clean(self):
        errors = {}

        if not self.serial_number or not self.serial_number.strip():
            errors["serial_number"] = "Serial number is required."
        if not self.part_number or not self.part_number.strip():
            errors["part_number"] = "Part number is required."
        if not self.description or not self.description.strip():
            errors["description"] = "Description is required."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.serial_number


class WorkOrder(models.Model):
    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("CLOSED", "Closed"),
    ]

    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name="workorders")
    wo_number = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="OPEN")
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        errors = {}
        now = timezone.now()

        if not self.part_id:
            errors["part"] = "Part is required."
        if not self.wo_number or not self.wo_number.strip():
            errors["wo_number"] = "Work order number is required."
        if not self.status:
            errors["status"] = "Status is required."

        if self.status == "CLOSED":
            if not self.closed_at:
                errors["closed_at"] = "Closed work order must have a close date."
            elif self.closed_at >= now:
                errors["closed_at"] = "A closed work order's close date must be in the past."

        # Rule: only one OPEN work order per part at a time
        if self.status == "OPEN" and self.part_id:
            duplicate_qs = WorkOrder.objects.filter(part_id=self.part_id, status="OPEN")
            if self.pk:
                duplicate_qs = duplicate_qs.exclude(pk=self.pk)
            if duplicate_qs.exists():
                errors["status"] = "This part already has an open work order."
    
        # Rule: WO can only be closed if all steps are DONE and a PASS inspection exists
        if self.status == "CLOSED":
            pending_steps = self.steps.filter(status="PENDING")
            if pending_steps.exists():
                errors["status"] = (
                    errors.get("status", "")
                    + " Cannot close: work order has pending steps."
                ).strip()

            has_pass = self.inspections.filter(result="PASS").exists()
            if not has_pass:
                errors["status"] = (
                    errors.get("status", "")
                    + " Cannot close: no passing inspection recorded."
                ).strip()

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()

        is_new = self.pk is None
        old_status = None
        if not is_new:
            old = WorkOrder.objects.get(pk=self.pk)
            old_status = old.status

        super().save(*args, **kwargs)

        if is_new:
            ActivityLog.objects.create(work_order=self, event="WO_OPENED")
        elif old_status != "CLOSED" and self.status == "CLOSED":
            ActivityLog.objects.create(work_order=self, event="WO_CLOSED")

    # NOTE: WO_DELETED is not logged here because ActivityLog rows are
    # cascade-deleted along with the WorkOrder, making the entry pointless.
    # If you need a persistent audit trail for deletions, move ActivityLog
    # to a separate table with SET_NULL or use a dedicated audit model.

    def __str__(self):
        return self.wo_number


class RepairStep(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("DONE", "Done"),
    ]

    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="steps")
    step_no = models.IntegerField()
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")

    def clean(self):
        errors = {}

        if not self.work_order_id:
            errors["work_order"] = "Work order is required."
        if self.step_no is None:
            errors["step_no"] = "Step number is required."
        elif self.step_no <= 0:
            errors["step_no"] = "Step number must be 1 or above."
        if not self.name or not self.name.strip():
            errors["name"] = "Step name is required."
        if not self.status:
            errors["status"] = "Status is required."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()

        is_new = self.pk is None
        old_status = None
        if not is_new:
            old = RepairStep.objects.get(pk=self.pk)
            old_status = old.status

        super().save(*args, **kwargs)

        if is_new:
            ActivityLog.objects.create(work_order=self.work_order, event="STEP_ADDED")
        elif old_status != "DONE" and self.status == "DONE":
            ActivityLog.objects.create(work_order=self.work_order, event="STEP_DONE")

    def delete(self, *args, **kwargs):
        work_order = self.work_order
        super().delete(*args, **kwargs)
        ActivityLog.objects.create(work_order=work_order, event="STEP_DELETED")

    class Meta:
        unique_together = ("work_order", "step_no")

    def __str__(self):
        return f"{self.work_order.wo_number} - Step {self.step_no}"


class Inspection(models.Model):
    RESULT_CHOICES = [
        ("PASS", "Pass"),
        ("FAIL", "Fail"),
    ]

    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="inspections")
    inspector_name = models.CharField(max_length=100)
    result = models.CharField(max_length=10, choices=RESULT_CHOICES)
    notes = models.TextField(blank=True)

    def clean(self):
        errors = {}

        if not self.work_order_id:
            errors["work_order"] = "Work order is required."
        if not self.inspector_name or not self.inspector_name.strip():
            errors["inspector_name"] = "Inspector name is required."
        if not self.result:
            errors["result"] = "Result is required."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()

        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            ActivityLog.objects.create(work_order=self.work_order, event="INSPECTION_RECORDED")

    def delete(self, *args, **kwargs):
        work_order = self.work_order
        super().delete(*args, **kwargs)
        ActivityLog.objects.create(work_order=work_order, event="INSPECTION_DELETED")

    def __str__(self):
        return f"{self.work_order.wo_number} - {self.result}"


class ActivityLog(models.Model):
    EVENT_CHOICES = [
        ("WO_OPENED", "Work Order Opened"),
        ("WO_CLOSED", "Work Order Closed"),
        ("STEP_ADDED", "Step Added"),
        ("STEP_DONE", "Step Done"),
        ("STEP_DELETED", "Step Deleted"),
        ("INSPECTION_RECORDED", "Inspection Recorded"),
        ("INSPECTION_DELETED", "Inspection Deleted"),
    ]

    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="activities")
    event = models.CharField(max_length=50, choices=EVENT_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    actor = models.CharField(max_length=100, default="system")

    def clean(self):
        errors = {}

        if not self.work_order_id:
            errors["work_order"] = "Work order is required."
        if not self.event:
            errors["event"] = "Event is required."
        if not self.actor or not self.actor.strip():
            errors["actor"] = "Actor is required."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.work_order.wo_number} - {self.event}"