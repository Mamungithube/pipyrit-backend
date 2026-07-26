"""
quizzes/services.py
~~~~~~~~~~~~~~~~~~~
Business logic for Quiz and Interview flows.
Views remain thin — they only handle HTTP; all calculations live here.
"""

from django.db.models import Avg
from django.shortcuts import get_object_or_404

from .models import (
    QuizQuestion, QuizOption, UserQuizResult,
    InterviewQuestion, InterviewOption, InterviewResult,
)


# ── Shared Helper ────────────────────────────────────────────────────────────

def recalculate_confidence(user) -> int:
    """
    Returns a combined confidence score (0-100) calculated from the
    weighted average of all quiz and interview results for the user.
    Used to keep Profile.confidence_level consistent across both flows.
    """
    quiz_qs = UserQuizResult.objects.filter(user=user)
    interview_qs = InterviewResult.objects.filter(user=user)

    quiz_avg = quiz_qs.aggregate(avg=Avg('confidence_level'))['avg'] or 0
    interview_avg = interview_qs.aggregate(avg=Avg('confidence_level'))['avg'] or 0

    quiz_count = quiz_qs.count()
    interview_count = interview_qs.count()
    total_count = quiz_count + interview_count

    if total_count == 0:
        return 0

    combined_avg = (
        (quiz_avg * quiz_count) + (interview_avg * interview_count)
    ) / total_count

    return min(round(combined_avg), 100)


# ── Quiz Services ─────────────────────────────────────────────────────────────

def submit_quiz(user, user_answers: list) -> dict:
    """
    Scores a submitted quiz.

    Bulk-fetches all questions and options to avoid N+1 queries,
    creates a UserQuizResult, and updates the user's profile points.

    Returns a dict ready to be passed directly to api_response().
    """
    total_earned_points = 0
    correct_answers_count = 0
    total_questions = len(user_answers)

    q_ids = [item.get('question_id') for item in user_answers]
    o_ids = [item.get('option_id') for item in user_answers]

    questions_map = {q.id: q for q in QuizQuestion.objects.filter(id__in=q_ids)}
    options_map = {
        o.id: o
        for o in QuizOption.objects.filter(id__in=o_ids).select_related('question')
    }

    for item in user_answers:
        question = questions_map.get(item.get('question_id'))
        selected_option = options_map.get(item.get('option_id'))
        if question and selected_option and selected_option.question_id == question.id:
            if selected_option.is_correct:
                correct_answers_count += 1
                total_earned_points += question.points

    result = UserQuizResult.objects.create(
        user=user,
        total_questions=total_questions,
        correct_answers=correct_answers_count,
        total_points_earned=total_earned_points,
    )
    result.questions.set(q_ids)

    profile = user.profile
    profile.total_points += total_earned_points
    profile.save()

    return {
        "correct_answers": correct_answers_count,
        "total_questions": total_questions,
        "points_earned": total_earned_points,
        "total_profile_points": profile.total_points,
    }


def save_quiz_score(user, result_id: int, data: dict) -> UserQuizResult:
    """
    Persists a score sent from the client (used when scoring happens client-side).
    Adjusts profile points by the delta (new - old) and recalculates confidence.

    Returns the updated UserQuizResult instance.
    """
    correct = data.get('correct_answers', 0)
    total = data.get('total_questions', 25)
    points = data.get('earned_points', 0)
    confidence = data.get('confidence_level', 0)

    result = get_object_or_404(UserQuizResult, id=result_id, user=user)

    old_points = result.total_points_earned
    result.correct_answers = correct
    result.total_questions = total
    result.total_points_earned = points
    result.confidence_level = confidence
    result.save()

    profile = user.profile
    profile.total_points += (points - old_points)
    profile.confidence_level = recalculate_confidence(user)
    profile.save()

    return result


# ── Interview Services ────────────────────────────────────────────────────────

def submit_interview(user, user_answers: list, category_id, level: str) -> InterviewResult:
    """
    Scores a submitted mock interview.

    Bulk-fetches all questions and options to avoid N+1 queries,
    creates an InterviewResult, and updates the user's profile.

    Returns the created InterviewResult instance.
    """
    total_earned_points = 0
    correct_answers_count = 0

    q_ids = [item.get('question_id') for item in user_answers]
    o_ids = [item.get('option_id') for item in user_answers]

    questions_map = {
        q.id: q for q in InterviewQuestion.objects.filter(id__in=q_ids)
    }
    options_map = {
        o.id: o
        for o in InterviewOption.objects.filter(id__in=o_ids).select_related('question')
    }

    for item in user_answers:
        question = questions_map.get(item.get('question_id'))
        selected_option = options_map.get(item.get('option_id'))
        if question and selected_option and selected_option.question_id == question.id:
            if selected_option.is_correct:
                correct_answers_count += 1
                total_earned_points += question.points

    total_qs = len(user_answers) if len(user_answers) > 0 else 1
    confidence = int((correct_answers_count / total_qs) * 100)

    result = InterviewResult.objects.create(
        user=user,
        category_id=category_id,
        level=level,
        total_questions=len(user_answers),
        correct_answers=correct_answers_count,
        total_points_earned=total_earned_points,
        confidence_level=confidence,
    )
    result.questions.set(q_ids)

    profile = user.profile
    profile.total_points += total_earned_points
    profile.confidence_level = recalculate_confidence(user)
    profile.save()

    return result


def save_interview_score(user, result_id: int, data: dict) -> InterviewResult:
    """
    Persists an interview score sent from the client.
    Adjusts profile points by the delta and recalculates confidence.

    Returns the updated InterviewResult instance.
    """
    correct = data.get('correct_answers', 0)
    total = data.get('total_questions', 25)
    points = data.get('earned_points', 0)
    confidence = data.get('confidence_level', 0)

    result = get_object_or_404(InterviewResult, id=result_id, user=user)

    old_points = result.total_points_earned
    result.correct_answers = correct
    result.total_questions = total
    result.total_points_earned = points
    result.confidence_level = confidence
    result.save()

    profile = user.profile
    profile.total_points += (points - old_points)
    profile.confidence_level = recalculate_confidence(user)
    profile.save()

    return result
