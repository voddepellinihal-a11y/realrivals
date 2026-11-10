"""Tests for editing a challenge after it has been created."""
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.modules.challenge import service as challenge_service


def make_user(user_id="user-id"):
    user = MagicMock()
    user.id = user_id
    return user


def make_challenge(creator_id="user-id", **kwargs):
    challenge = MagicMock()
    challenge.creator_id = creator_id
    challenge.title = kwargs.get("title", "Old title")
    challenge.description = kwargs.get("description", "Old description")
    challenge.category = kwargs.get("category", "health")
    challenge.difficulty = kwargs.get("difficulty", "medium")
    challenge.base_xp = kwargs.get("base_xp", 40)
    challenge.proof_type = kwargs.get("proof_type", "photo")
    return challenge


class EditOwnershipTestCase(unittest.TestCase):
    def test_creator_may_edit_their_challenge(self):
        user = make_user()
        challenge = make_challenge(creator_id=user.id)
        challenge_service.assert_can_edit(user, challenge)

    def test_non_creator_is_rejected(self):
        user = make_user()
        challenge = make_challenge(creator_id="somebody-else")

        with self.assertRaises(HTTPException) as ctx:
            challenge_service.assert_can_edit(user, challenge)

        self.assertEqual(ctx.exception.status_code, 403)

    def test_missing_challenge_is_a_404(self):
        user = make_user()

        with self.assertRaises(HTTPException) as ctx:
            challenge_service.assert_can_edit(user, None)

        self.assertEqual(ctx.exception.status_code, 404)


class ApplyEditsTestCase(unittest.TestCase):
    def test_title_description_and_xp_are_updated(self):
        challenge = make_challenge()
        updated = challenge_service.apply_edits(
            challenge,
            {
                "title": "New title",
                "description": "New description",
                "base_xp": 120,
                "category": "fitness",
                "difficulty": "hard",
                "proof_type": "text",
            },
        )

        self.assertEqual(updated.title, "New title")
        self.assertEqual(updated.description, "New description")
        self.assertEqual(updated.base_xp, 120)
        self.assertEqual(updated.category, "fitness")
        self.assertEqual(updated.difficulty, "hard")
        self.assertEqual(updated.proof_type, "text")

    def test_untouched_fields_keep_their_values(self):
        challenge = make_challenge()
        updated = challenge_service.apply_edits(challenge, {"title": "Only the title"})

        self.assertEqual(updated.title, "Only the title")
        self.assertEqual(updated.description, "Old description")
        self.assertEqual(updated.base_xp, 40)

    def test_blank_title_is_ignored(self):
        challenge = make_challenge()
        updated = challenge_service.apply_edits(challenge, {"title": "   "})

        self.assertEqual(updated.title, "Old title")

    def test_title_is_trimmed(self):
        challenge = make_challenge()
        updated = challenge_service.apply_edits(challenge, {"title": "  Padded  "})

        self.assertEqual(updated.title, "Padded")

    def test_invalid_xp_is_rejected(self):
        challenge = make_challenge()

        with self.assertRaises(HTTPException) as ctx:
            challenge_service.apply_edits(challenge, {"base_xp": "not-a-number"})

        self.assertEqual(ctx.exception.status_code, 400)

    def test_negative_xp_is_rejected(self):
        challenge = make_challenge()

        with self.assertRaises(HTTPException) as ctx:
            challenge_service.apply_edits(challenge, {"base_xp": -5})

        self.assertEqual(ctx.exception.status_code, 400)

    def test_proof_type_must_be_known(self):
        challenge = make_challenge()

        with self.assertRaises(HTTPException) as ctx:
            challenge_service.apply_edits(challenge, {"proof_type": "hologram"})

        self.assertEqual(ctx.exception.status_code, 400)

    def test_empty_payload_changes_nothing(self):
        challenge = make_challenge()
        updated = challenge_service.apply_edits(challenge, {})

        self.assertEqual(updated.title, "Old title")
        self.assertEqual(updated.base_xp, 40)


if __name__ == "__main__":
    unittest.main()
