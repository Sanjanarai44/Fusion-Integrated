# Generated manually for the ELM pilot. Verify with makemigrations --check.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="LeaveType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(choices=[("CL", "Casual Leave"), ("RH", "Restricted Holiday"), ("SCL", "Special Casual Leave"), ("EL", "Earned Leave"), ("COL", "Compensatory Leave"), ("VL", "Vacation Leave")], max_length=3, unique=True)),
                ("name", models.CharField(max_length=80)),
                ("requires_substitute", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"ordering": ["code"]},
        ),
        migrations.CreateModel(
            name="CalendarDay",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(unique=True)),
                ("label", models.CharField(blank=True, max_length=120)),
                ("is_closed", models.BooleanField(default=False)),
                ("is_restricted_holiday", models.BooleanField(default=False)),
                ("is_academic_vacation", models.BooleanField(default=False)),
                ("is_published", models.BooleanField(default=False)),
            ],
            options={"ordering": ["date"]},
        ),
        migrations.CreateModel(
            name="LeavePolicy",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("employee_category", models.CharField(default="all", max_length=40)),
                ("annual_entitlement", models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ("carry_forward", models.BooleanField(default=False)),
                ("effective_from", models.DateField()),
                ("effective_to", models.DateField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("leave_type", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="policies", to="elm.leavetype")),
            ],
            options={"ordering": ["leave_type__code", "effective_from"]},
        ),
        migrations.AddConstraint(
            model_name="leavepolicy",
            constraint=models.UniqueConstraint(fields=("leave_type", "employee_category", "effective_from"), name="elm_policy_effective_start_unique"),
        ),
        migrations.CreateModel(
            name="LeaveBalance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("employee_id", models.PositiveBigIntegerField(db_index=True)),
                ("year", models.PositiveSmallIntegerField(default=2026)),
                ("entitled_days", models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ("used_days", models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ("reserved_days", models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ("leave_type", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="balances", to="elm.leavetype")),
            ],
            options={"ordering": ["year", "leave_type__code"]},
        ),
        migrations.AddConstraint(
            model_name="leavebalance",
            constraint=models.UniqueConstraint(fields=("employee_id", "leave_type", "year"), name="elm_unique_employee_leave_year"),
        ),
        migrations.CreateModel(
            name="LeaveApplication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("employee_id", models.PositiveBigIntegerField(db_index=True)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("is_half_day", models.BooleanField(default=False)),
                ("half_day_period", models.CharField(blank=True, choices=[("first", "First Half"), ("second", "Second Half")], max_length=6)),
                ("reason", models.TextField()),
                ("station_leave", models.BooleanField(default=False)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("pending_substitute", "Awaiting Substitute Consent"), ("pending_review", "Pending Review"), ("recommended", "Recommended"), ("approved", "Approved"), ("rejected", "Rejected"), ("withdrawn", "Withdrawn"), ("cancellation_pending", "Cancellation Pending"), ("cancelled", "Cancelled")], default="draft", max_length=24)),
                ("reviewer_employee_id", models.PositiveBigIntegerField(blank=True, null=True)),
                ("decision_note", models.TextField(blank=True)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("decision_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("leave_type", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="applications", to="elm.leavetype")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="leaveapplication",
            index=models.Index(fields=["employee_id", "status"], name="elm_emp_status_idx"),
        ),
        migrations.AddIndex(
            model_name="leaveapplication",
            index=models.Index(fields=["start_date", "end_date"], name="elm_dates_idx"),
        ),
        migrations.CreateModel(
            name="SubstituteNomination",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("substitute_employee_id", models.PositiveBigIntegerField(db_index=True)),
                ("status", models.CharField(choices=[("pending", "Pending Response"), ("accepted", "Accepted"), ("declined", "Declined")], default="pending", max_length=10)),
                ("responded_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("application", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="substitute_nomination", to="elm.leaveapplication")),
            ],
        ),
    ]
