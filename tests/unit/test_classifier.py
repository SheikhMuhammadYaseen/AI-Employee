"""Tests for the item classifier — Silver Tier (T019)."""

import pytest

from src.reasoning.classifier import classify


class TestSimpleClassification:
    def test_simple_greeting(self):
        fm = {"subject": "Hello"}
        body = "Just wanted to say hi."
        assert classify(fm, body) == "simple"

    def test_simple_notification(self):
        fm = {"subject": "Update received"}
        body = "Your order has been shipped."
        assert classify(fm, body) == "simple"


class TestComplexClassification:
    def test_numbered_list_is_complex(self):
        fm = {"subject": "Project plan"}
        body = "1. Gather requirements\n2. Design solution\n3. Implement code\n4. Test"
        assert classify(fm, body) == "complex"

    def test_multiple_action_verbs_is_complex(self):
        fm = {"subject": "Weekly tasks"}
        body = "Please review the document, prepare a summary, and update the tracker."
        assert classify(fm, body) == "complex"

    def test_complex_keywords_trigger(self):
        fm = {"subject": "Prepare report"}
        body = "We need to compile the data and organize the findings into steps."
        assert classify(fm, body) == "complex"


class TestActionRequiredClassification:
    def test_reply_keyword(self):
        fm = {"subject": "Client email"}
        body = "Please reply to the client and send the invoice."
        assert classify(fm, body) == "action_required"

    def test_send_keyword(self):
        fm = {"subject": "Forward invoice"}
        body = "Forward this email to accounting and send a copy to the manager."
        assert classify(fm, body) == "action_required"

    def test_post_and_publish(self):
        fm = {"subject": "Social media"}
        body = "Post the announcement and share it on all channels."
        assert classify(fm, body) == "action_required"


class TestPresetClassification:
    def test_existing_classification_respected(self):
        fm = {"classification": "complex", "subject": "Anything"}
        body = "This body is simple."
        assert classify(fm, body) == "complex"

    def test_existing_action_required_respected(self):
        fm = {"classification": "action_required", "subject": "Test"}
        body = "Nothing special here."
        assert classify(fm, body) == "action_required"


class TestEdgeCases:
    def test_empty_body(self):
        fm = {"subject": "Empty"}
        body = ""
        assert classify(fm, body) == "simple"

    def test_empty_frontmatter_and_body(self):
        fm = {}
        body = ""
        assert classify(fm, body) == "simple"

    def test_subject_keywords_counted(self):
        fm = {"subject": "Reply to urgent email and send invoice"}
        body = ""
        assert classify(fm, body) == "action_required"
