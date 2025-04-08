from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from marketing.models import Admission
from finance.models import ProgramFees, FinanceStatement, AdmissionFinance
from academic_program.models import Program


@receiver(post_save, sender=Admission)
def create_admission_finance(sender, instance, created, **kwargs):
    """
    When a new Admission is created, this signal finds the active Program
    under the admission’s program_of_interest, retrieves the related fees and
    finance statement, and then creates an AdmissionFinance record.
    """
    if created:
        # Get current date
        today = timezone.now().date()

        # Find active programs for the given ProgramCover (program_of_interest)
        active_programs = Program.objects.filter(
            program_cover=instance.program_of_interest,
            flag=True,
            program_ended=False,
            start_date__lte=today,
            end_date__gte=today
        ).order_by('start_date')

        if active_programs.exists():
            active_program = active_programs.first()  # choose the earliest active program

            try:
                program_fees = ProgramFees.objects.get(program=active_program)
            except ProgramFees.DoesNotExist:
                program_fees = None

            if program_fees:
                try:
                    finance_statement = FinanceStatement.objects.get(program_fees=program_fees)
                except FinanceStatement.DoesNotExist:
                    finance_statement = None

                if finance_statement:
                    # Create the AdmissionFinance record if it doesn't exist yet.
                    if not AdmissionFinance.objects.filter(student=instance).exists():
                        AdmissionFinance.objects.create(
                            student=instance,
                            fees_paid=0.0,
                            fees=finance_statement
                        )
