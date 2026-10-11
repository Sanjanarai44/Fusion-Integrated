"""Initial domain models for Employee Leave Management (ELM).

This is a pilot implementation. Policy configuration, institutional hierarchy,
workflow transitions, and integration with the academic calendar remain follow-up work.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class LeaveType(models.Model):
    class Code(models.TextChoices):
        CL = "CL", "Casual Leave"
        RH = "RH", "Restricted Holiday"
        SCL = "SCL", "Special Casual Leave"
        EL = "EL", "Earned Leave"
        COL = "COL", "Compensatory Leave"
        VL = "VL", "Vacation Leave"

    code = models.CharField(max_length=3, choices=Code.choices, unique=True)
    name = models.CharField(max_length=80)
    requires_substitute = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class LeaveBalance(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name="elm_leave_balances")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT,
                                   related_name="balances")
    year = models.PositiveSmallIntegerField(default=timezone.localdate().year)
    entitled_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    used_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["employee", "leave_type", "year"], name="elm_unique_employee_leave_year"
        )]
        ordering = ["year", "leave_type__code"]

    @property
    def available_days(self):
        return self.entitled_days - self.used_days

    def __str__(self):
        return f"{self.employee_id}: {self.leave_type.code} ({self.year})"


class LeaveApplication(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        PENDING = "pending", "Pending Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name="elm_leave_applications")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT,
                                   related_name="applications")
    start_date = models.DateField()
    end_date = models.DateField()
    is_half_day = models.BooleanField(default=False)
    reason = models.TextField()
    station_leave = models.BooleanField(default=False)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be before start date."})
        if self.is_half_day and self.start_date != self.end_date:
            raise ValidationError({"is_half_day": "A half-day application must cover one date."})

    def __str__(self):
        return f"Leave #{self.pk or 'new'} - {self.employee_id}"


class SubstituteNomination(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending Response"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    application = models.OneToOneField(LeaveApplication, on_delete=models.CASCADE,
                                       related_name="substitute_nomination")
    substitute = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                   related_name="elm_substitute_nominations")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Substitute for leave #{self.application_id}: {self.status}"
