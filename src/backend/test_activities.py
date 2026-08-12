import unittest

from fastapi import HTTPException

from src.backend.routers import activities as activities_router


class FakeCollection:
    def __init__(self, items):
        self.items = items

    def find(self, query):
        return [dict(item) for item in self.items if self._matches(item, query)]

    def _matches(self, item, query):
        for key, value in query.items():
            if key == "$or":
                if not any(self._matches(item, clause) for clause in value):
                    return False
                continue

            current = item
            for part in key.split("."):
                if part not in current:
                    current = None
                    break
                current = current[part]

            if isinstance(value, dict):
                if "$in" in value:
                    if isinstance(current, list):
                        if not any(entry in value["$in"] for entry in current):
                            return False
                    elif current not in value["$in"]:
                        return False
                elif "$gte" in value:
                    if current is None or current < value["$gte"]:
                        return False
                elif "$lte" in value:
                    if current is None or current > value["$lte"]:
                        return False
                elif "$exists" in value:
                    exists = current is not None
                    if exists != value["$exists"]:
                        return False
            elif current != value:
                return False

        return True


class GetActivitiesDifficultyTests(unittest.TestCase):
    def setUp(self):
        self.original_collection = activities_router.activities_collection
        activities_router.activities_collection = FakeCollection(
            [
                {
                    "_id": "Chess Club",
                    "description": "Open to everyone",
                    "schedule": "Mondays",
                    "schedule_details": {
                        "days": ["Monday"],
                        "start_time": "15:00",
                        "end_time": "16:00",
                    },
                    "max_participants": 10,
                    "participants": [],
                },
                {
                    "_id": "Programming Class",
                    "description": "Learn programming fundamentals",
                    "difficulty": "Beginner",
                    "schedule": "Tuesdays",
                    "schedule_details": {
                        "days": ["Tuesday"],
                        "start_time": "07:00",
                        "end_time": "08:00",
                    },
                    "max_participants": 10,
                    "participants": [],
                },
                {
                    "_id": "Math Club",
                    "description": "Challenge problems",
                    "difficulty": "Advanced",
                    "schedule": "Tuesdays",
                    "schedule_details": {
                        "days": ["Tuesday"],
                        "start_time": "07:15",
                        "end_time": "08:00",
                    },
                    "max_participants": 10,
                    "participants": [],
                },
            ]
        )

    def tearDown(self):
        activities_router.activities_collection = self.original_collection

    def test_all_levels_filter_only_returns_unspecified_difficulty(self):
        activities = activities_router.get_activities(difficulty="all-levels")

        self.assertEqual(set(activities.keys()), {"Chess Club"})

    def test_specific_difficulty_filter_can_be_combined_with_day(self):
        activities = activities_router.get_activities(
            day="Tuesday", difficulty="Beginner"
        )

        self.assertEqual(set(activities.keys()), {"Programming Class"})

    def test_invalid_difficulty_filter_is_rejected(self):
        with self.assertRaises(HTTPException) as context:
            activities_router.get_activities(difficulty="Expert")

        self.assertEqual(context.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
