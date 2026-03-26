from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .models import Part, WorkOrder, RepairStep, Inspection


class WorkOrderModelTests(TestCase):
    def setUp(self):
        self.part = Part.objects.create(
            serial_number="SN-001",
            part_number="PN-001",
            description="Test part",
        )

    def test_only_one_open_work_order_per_part(self):
        WorkOrder.objects.create(
            part=self.part,
            wo_number="WO-001",
            status="OPEN",
        )

        second_open = WorkOrder(
            part=self.part,
            wo_number="WO-002",
            status="OPEN",
        )

        with self.assertRaises(ValidationError):
            second_open.full_clean()

    def test_cannot_close_work_order_without_done_steps_and_pass_inspection(self):
        wo = WorkOrder.objects.create(
            part=self.part,
            wo_number="WO-003",
            status="OPEN",
        )

        RepairStep.objects.create(
            work_order=wo,
            step_no=1,
            name="Initial inspection",
            status="PENDING",
        )

        Inspection.objects.create(
            work_order=wo,
            inspector_name="Alice",
            result="FAIL",
            notes="Not ready",
        )

        wo.status = "CLOSED"
        wo.closed_at = timezone.now() - timezone.timedelta(minutes=1)

        with self.assertRaises(ValidationError):
            wo.full_clean()

    def test_step_number_must_be_unique_within_work_order(self):
        wo = WorkOrder.objects.create(
            part=self.part,
            wo_number="WO-004",
            status="OPEN",
        )

        RepairStep.objects.create(
            work_order=wo,
            step_no=1,
            name="Disassembly",
            status="PENDING",
        )

        duplicate_step = RepairStep(
            work_order=wo,
            step_no=1,
            name="Cleaning",
            status="PENDING",
        )

        with self.assertRaises(ValidationError):
            duplicate_step.validate_unique()