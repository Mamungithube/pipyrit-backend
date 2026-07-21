from django.core.management.base import BaseCommand
from django.db.models import Sum
from user.models import Profile
from quizzes.models import UserQuizResult, InterviewResult


class Command(BaseCommand):
    help = "Recalculate profile.total_points from actual sum of quiz + interview results"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would change without saving',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        profiles = Profile.objects.all()
        fixed_count = 0

        for profile in profiles:
            user_id = profile.user_id

            quiz_sum = UserQuizResult.objects.filter(
                user_id=user_id
            ).aggregate(total=Sum('total_points_earned'))['total'] or 0

            interview_sum = InterviewResult.objects.filter(
                user_id=user_id
            ).aggregate(total=Sum('total_points_earned'))['total'] or 0

            correct_total = quiz_sum + interview_sum
            old_value = profile.total_points

            if old_value != correct_total:
                fixed_count += 1
                self.stdout.write(
                    f"user_id={user_id}: {old_value} -> {correct_total} "
                    f"(quiz={quiz_sum}, interview={interview_sum})"
                )
                if not dry_run:
                    profile.total_points = correct_total
                    profile.save(update_fields=['total_points'])

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"\nDRY RUN: {fixed_count} profile(s) would be corrected."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\nDone: {fixed_count} profile(s) corrected."
            ))
