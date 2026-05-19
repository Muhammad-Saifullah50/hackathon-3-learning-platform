"""Integration tests for GET /api/v1/dashboard/teacher/analytics (F019)."""

from unittest.mock import AsyncMock, MagicMock
import uuid

import pytest
from fastapi.testclient import TestClient

from src.auth.dependencies import get_current_user
from src.dependencies import get_analytics_repository
from src.main import app
from src.models.user import User

ANALYTICS_URL = "/api/v1/dashboard/teacher/analytics"

# ------------------------------------------------------------------
# Shared fixtures
# ------------------------------------------------------------------

MODULE_MASTERY_ROWS = [
    {"module_slug": "basics", "module_name": "Basics", "avg_score": 78.0},
    {"module_slug": "control_flow", "module_name": "Control Flow", "avg_score": 65.0},
    {"module_slug": "data_structures", "module_name": "Data Structures", "avg_score": 58.0},
    {"module_slug": "functions", "module_name": "Functions", "avg_score": 52.0},
    {"module_slug": "oop", "module_name": "OOP", "avg_score": 44.0},
    {"module_slug": "files", "module_name": "Files", "avg_score": 38.0},
    {"module_slug": "errors", "module_name": "Errors", "avg_score": 33.0},
    {"module_slug": "libraries", "module_name": "Libraries", "avg_score": 22.0},
]


def _make_repo(
    total_students: int = 5,
    avg_mastery: float | None = 55.0,
    low_quiz_count: int = 1,
    module_rows: list | None = None,
    struggling_rows: list | None = None,
) -> MagicMock:
    repo = MagicMock()
    repo.get_total_students = AsyncMock(return_value=total_students)
    repo.get_avg_mastery = AsyncMock(return_value=avg_mastery)
    repo.get_low_quiz_count = AsyncMock(return_value=low_quiz_count)
    repo.get_module_mastery_breakdown = AsyncMock(return_value=module_rows or MODULE_MASTERY_ROWS)
    repo.get_struggling_students = AsyncMock(return_value=struggling_rows or [])
    return repo


def _teacher_user() -> User:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.role = "teacher"
    user.display_name = "Test Teacher"
    return user


def _student_user() -> User:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.role = "student"
    user.display_name = "Test Student"
    return user


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------

class TestTeacherAnalyticsAuth:
    def test_no_auth_returns_401_or_403(self):
        with TestClient(app) as client:
            response = client.get(ANALYTICS_URL)
        assert response.status_code in (401, 403)

    def test_student_token_returns_403(self):
        repo = _make_repo()
        app.dependency_overrides[get_current_user] = lambda: _student_user()
        app.dependency_overrides[get_analytics_repository] = lambda: repo
        try:
            with TestClient(app) as client:
                response = client.get(ANALYTICS_URL, headers={"Authorization": "Bearer fake"})
            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()

    def test_teacher_token_returns_200(self):
        repo = _make_repo()
        app.dependency_overrides[get_current_user] = lambda: _teacher_user()
        app.dependency_overrides[get_analytics_repository] = lambda: repo
        try:
            with TestClient(app) as client:
                response = client.get(ANALYTICS_URL, headers={"Authorization": "Bearer fake"})
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()


class TestTeacherAnalyticsResponse:
    def _get(self, repo: MagicMock) -> dict:
        app.dependency_overrides[get_current_user] = lambda: _teacher_user()
        app.dependency_overrides[get_analytics_repository] = lambda: repo
        try:
            with TestClient(app) as client:
                response = client.get(ANALYTICS_URL, headers={"Authorization": "Bearer fake"})
            assert response.status_code == 200
            return response.json()
        finally:
            app.dependency_overrides.clear()

    def test_total_students_matches_repo(self):
        repo = _make_repo(total_students=12)
        data = self._get(repo)
        assert data["total_students"] == 12

    def test_avg_mastery_null_when_no_records(self):
        repo = _make_repo(avg_mastery=None)
        data = self._get(repo)
        assert data["avg_mastery"] is None

    def test_avg_mastery_returned_when_present(self):
        repo = _make_repo(avg_mastery=67.5)
        data = self._get(repo)
        assert data["avg_mastery"] == pytest.approx(67.5)

    def test_all_8_modules_present_in_breakdown(self):
        repo = _make_repo()
        data = self._get(repo)
        assert len(data["module_mastery"]) == 8
        slugs = {m["module_slug"] for m in data["module_mastery"]}
        expected = {"basics", "control_flow", "data_structures", "functions", "oop", "files", "errors", "libraries"}
        assert slugs == expected

    def test_missing_module_shows_zero(self):
        # Simulate a module with no mastery records (avg_score = 0.0)
        rows = [dict(r) for r in MODULE_MASTERY_ROWS]
        rows[0]["avg_score"] = 0.0  # 'basics' has no records
        repo = _make_repo(module_rows=rows)
        data = self._get(repo)
        basics = next(m for m in data["module_mastery"] if m["module_slug"] == "basics")
        assert basics["avg_score"] == 0.0

    def test_student_with_49_appears_in_struggling(self):
        struggling = [
            {
                "student_id": str(uuid.uuid4()),
                "display_name": "Alice",
                "score": 49.0,
                "module_slug": "oop",
                "topic_label": "Inheritance",
            }
        ]
        repo = _make_repo(low_quiz_count=1, struggling_rows=struggling)
        data = self._get(repo)
        assert len(data["struggling_students"]) == 1
        assert data["struggling_students"][0]["score"] == pytest.approx(49.0)

    def test_student_with_50_does_not_appear(self):
        # Repository enforces the < 50 boundary; empty list means 50% student excluded
        repo = _make_repo(low_quiz_count=0, struggling_rows=[])
        data = self._get(repo)
        assert data["struggling_students"] == []

    def test_low_quiz_count_matches_repo(self):
        repo = _make_repo(low_quiz_count=3)
        data = self._get(repo)
        assert data["low_quiz_count"] == 3
