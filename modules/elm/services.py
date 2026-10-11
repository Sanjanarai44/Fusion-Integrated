"""Business rules for ELM's first backend pilot."""
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Q

from modules.elm.models import CalendarDay, LeaveApplication, LeaveBalance, LeaveType, SubstituteNomination


CONTINUOUS_LEAVE_CODES = {LeaveType.Code.EL, LeaveType.Code.COL, LeaveType.Code.VL}


def count_leave_days(start_date, end_date, leave_type_code, *, half_day=False):
    """Count days using continuous vs working-day rules."""
    if end_date < start_date:
        raise ValidationError({"end_date": "End date cannot be before start date."})
    if half_day:
        if start_date != end_date or leave_type_code != LeaveType.Code.CL:
            raise ValidationError("Half-day leave is supported for one-day CL only.")
        return Decimal("0.5")
    if leave_type_code in CONTINUOUS_LEAVE_CODES:
        return Decimal((end_date - start_date).days + 1)
    closed_dates = set(CalendarDay.objects.filter(
        date__gte=start_date, date__lte=end_date,
        is_published=True, is_closed=True,
    ).values_list("date", flat=True))
    days, current = 0, start_date
    while current <= end_date:
        if current.weekday() < 5 and current not in closed_dates:
            days += 1
        current += timedelta(days=1)
    return Decimal(days)


def validate_application(application):
    """Validate basic policy, balance, calendar, and overlap requirements."""
    application.full_clean()
    leave_type, code = application.leave_type, application.leave_type.code
    if not leave_type.is_active:
        raise ValidationError({"leave_type": "This leave type is inactive."})
    if code == LeaveType.Code.RH:
        if application.start_date != application.end_date:
            raise ValidationError({"end_date": "RH must be taken on one published RH date."})
        if not CalendarDay.objects.filter(
            date=application.start_date, is_published=True, is_restricted_holiday=True
        ).exists():
            raise ValidationError({"start_date": "Date is not a published restricted holiday."})

    active_statuses = [
        LeaveApplication.Status.PENDING_SUBSTITUTE,
        LeaveApplication.Status.PENDING_REVIEW,
        LeaveApplication.Status.RECOMMENDED,
        LeaveApplication.Status.APPROVED,
        LeaveApplication.Status.CANCELLATION_PENDING,
    ]
    overlap = LeaveApplication.objects.filter(
        employee_id=application.employee_id, status__in=active_statuses,
        start_date__lte=application.end_date, end_date__gte=application.start_date,
    )
    if application.pk:
        overlap = overlap.exclude(pk=application.pk)
    if application.is_half_day:
        overlap = overlap.filter(Q(is_half_day=False) | Q(half_day_period=application.half_day_period))
    if overlap.exists():
        raise ValidationError("Application overlaps another pending or approved leave.")

    requested = count_leave_days(
        application.start_date, application.end_date, code, half_day=application.is_half_day,
    )
    balance = LeaveBalance.objects.filter(
        employee_id=application.employee_id, leave_type=leave_type,
        year=application.start_date.year,
    ).first()
    if balance is None or balance.available_days < requested:
        raise ValidationError({"leave_type": "No sufficient recorded balance for this leave year."})
    return requested


def nominate_substitute(application, substitute_employee_id):
    if substitute_employee_id == application.employee_id:
        raise ValidationError({"substitute_employee_id": "Applicant cannot be their own substitute."})
    return SubstituteNomination.objects.update_or_create(
        application=application,
        defaults={"substitute_employee_id": substitute_employee_id,
                  "status": SubstituteNomination.Status.PENDING, "responded_at": None},
    )[0]


def respond_to_substitute(nomination, *, accepted):
    if nomination.status != SubstituteNomination.Status.PENDING:
        raise ValidationError("This nomination has already been answered.")
    from django.utils import timezone
    nomination.status = (SubstituteNomination.Status.ACCEPTED if accepted
                         else SubstituteNomination.Status.DECLINED)
    nomination.responded_at = timezone.now()
    nomination.save(update_fields=["status", "responded_at"])
    application = nomination.application
    if accepted and application.status == LeaveApplication.Status.PENDING_SUBSTITUTE:
        application.status = LeaveApplication.Status.PENDING_REVIEW
        application.save(update_fields=["status", "updated_at"])
    return nomination


def submit_application(application):
    if application.status != LeaveApplication.Status.DRAFT:
        raise ValidationError("Only a draft application can be submitted.")
    requested = validate_application(application)
    application.status = (LeaveApplication.Status.PENDING_SUBSTITUTE
                          if application.leave_type.requires_substitute
                          else LeaveApplication.Status.PENDING_REVIEW)
    from django.utils import timezone
    application.submitted_at = timezone.now()
    application.save()
    return requested
