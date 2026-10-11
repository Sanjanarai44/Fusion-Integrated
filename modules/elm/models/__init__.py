"""ELM domain models.

Employee identities belong to Fusion IAM, not this service's database. Store their
stable IAM numeric IDs rather than creating local auth.User foreign keys.
"""
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


class LeavePolicy(models.Model):
    """Effective policy values; policy changes are data, not hard-coded constants."""
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT,
                                   related_name="policies")
    employee_category = models.CharField(max_length=40, default="all")
    annual_entitlement = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    carry_forward = models.BooleanField(default=False)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["leave_type__code", "effective_from"]
        constraints = [
            models.UniqueConstraint(
                fields=["leave_type", "employee_category", "effective_from"],
                name="elm_policy_effective_start_unique",
            )
        ]

    def clean(self):
        super().clean()
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValidationError({"effective_to": "End date must not precede start date."})


class CalendarDay(models.Model):
    """A published calendar date; RH eligibility uses published RH dates only."""
    date = models.DateField(unique=True)
    label = models.CharField(max_length=120, blank=True)
    is_closed = models.BooleanField(default=False)
    is_restricted_holiday = models.BooleanField(default=False)
    is_academic_vacation = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return f"{self.date}: {self.label or 'Calendar day'}"


class LeaveBalance(models.Model):
    employee_id = models.PositiveBigIntegerField(db_index=True)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT,
                                   related_name="balances")
    year = models.PositiveSmallIntegerField(default=timezone.localdate().year)
    entitled_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    used_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    reserved_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["employee_id", "leave_type", "year"],
            name="elm_unique_employee_leave_year",
        )]
        ordering = ["year", "leave_type__code"]

    @property
    def available_days(self):
        return self.entitled_days - self.used_days - self.reserved_days

    def __str__(self):
        return f"{self.employee_id}: {self.leave_type.code} ({self.year})"


class LeaveApplication(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING_SUBSTITUTE = "pending_substitute", "Awaiting Substitute Consent"
        PENDING_REVIEW = "pending_review", "Pending Review"
        RECOMMENDED = "recommended", "Recommended"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"
        CANCELLATION_PENDING = "cancellation_pending", "Cancellation Pending"
        CANCELLED = "cancelled", "Cancelled"

    class HalfDayPeriod(models.TextChoices):
        FIRST = "first", "First Half"
        SECOND = "second", "Second Half"

    employee_id = models.PositiveBigIntegerField(db_index=True)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT,
                                   related_name="applications")
    start_date = models.DateField()
    end_date = models.DateField()
    is_half_day = models.BooleanField(default=False)
    half_day_period = models.CharField(max_length=6, choices=HalfDayPeriod.choices,
                                       blank=True)
    reason = models.TextField()
    station_leave = models.BooleanField(default=False)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.DRAFT)
    reviewer_employee_id = models.PositiveBigIntegerField(null=True, blank=True)
    decision_note = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    decision_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["employee_id", "status"]),
            models.Index(fields=["start_date", "end_date"]),
        ]

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be before start date."})
        if self.is_half_day:
            if self.start_date != self.end_date:
                raise ValidationError({"is_half_day": "A half-day application must cover one date."})
            if self.leave_type_id and self.leave_type.code != LeaveType.Code.CL:
                raise ValidationError({"is_half_day": "Half-day applications are supported for CL only."})
            if not self.half_day_period:
                raise ValidationError({"half_day_period": "Choose first half or second half."})
        elif self.half_day_period:
            raise ValidationError({"half_day_period": "Select a half-day period only for half-day leave."})

    def __str__(self):
        return f"Leave #{self.pk or 'new'} - employee {self.employee_id}"


class SubstituteNomination(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending Response"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    application = models.OneToOneField(LeaveApplication, on_delete=models.CASCADE,
                                       related_name="substitute_nomination")
    substitute_employee_id = models.PositiveBigIntegerField(db_index=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.application_id and self.substitute_employee_id == self.application.employee_id:
            raise ValidationError({"substitute_employee_id": "Applicant cannot be their own substitute."})

    def __str__(self):
        return f"Substitute for leave #{self.application_id}: {self.status}"
