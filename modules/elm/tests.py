from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from modules.elm.models import CalendarDay, LeaveType
from modules.elm.services import count_leave_days


class LeaveDayCountingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        LeaveType.objects.create(code="CL", name="Casual Leave")
        LeaveType.objects.create(code="EL", name="Earned Leave")

    def test_continuous_leave_includes_weekends(self):
        self.assertEqual(count_leave_days(date(2026, 10, 9), date(2026, 10, 11), "EL"), Decimal("3"))

    def test_working_leave_skips_weekends(self):
        self.assertEqual(count_leave_days(date(2026, 10, 9), date(2026, 10, 12), "CL"), Decimal("2"))

    def test_published_closed_weekday_is_excluded(self):
        CalendarDay.objects.create(date=date(2026, 10, 12), label="Holiday",
                                   is_closed=True, is_published=True)
        self.assertEqual(count_leave_days(date(2026, 10, 9), date(2026, 10, 12), "CL"), Decimal("1"))

    def test_half_day_cl_counts_half(self):
        self.assertEqual(count_leave_days(date(2026, 10, 9), date(2026, 10, 9), "CL",
                                          half_day=True), Decimal("0.5"))

    def test_invalid_range_is_rejected(self):
        with self.assertRaises(ValidationError):
            count_leave_days(date(2026, 10, 12), date(2026, 10, 9), "CL")
