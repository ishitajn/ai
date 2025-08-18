import unittest
import json
from ..main import handler

class TestMainHandler(unittest.TestCase):

    def setUp(self):
        self.example_payload = {
          "matchId": "test_match_1",
          "scraped_data": {
            "myName": "Test User",
            "theirName": "Test Match",
            "theirProfile": "I enjoy long walks on the beach and testing software.",
            "theirLocationString": "San Francisco, USA",
            "conversationHistory": [
              {"role": "user", "content": "Hi there! How are you?", "date": "2023-01-01"},
              {"role": "assistant", "content": "I'm doing great, thanks for asking! I'm excited for our date.", "date": "2023-01-01"}
            ]
          },
          "ui_settings": {
            "useEnhancedNlp": False,
            "myLocation": "New York, USA",
            "myProfile": "I like building robust applications.",
            "local_model_name": None
          }
        }

    def test_handler_fast_mode(self):
        """Test that the handler runs in fast mode without crashing and returns a dict."""
        # Note: This test doesn't check for model downloads, which might be slow.
        # It relies on the fallback mechanisms we built in.
        result = handler(self.example_payload)
        self.assertIsInstance(result, dict)
        self.assertIn("sentiment", result)
        self.assertIn("topics", result)
        self.assertIn("recommended_actions", result)
        print("\nFast mode handler test completed successfully.")

    def test_handler_enhanced_mode_fallback(self):
        """Test that the handler runs in enhanced mode and falls back gracefully if models are not available."""
        self.example_payload["ui_settings"]["useEnhancedNlp"] = True
        # In a CI/CD environment without network access or where models are large,
        # this will test the fallback to the fast mode.
        result = handler(self.example_payload)
        self.assertIsInstance(result, dict)
        self.assertIn("sentiment", result)
        # Check if confidence is lower, indicating a potential fallback.
        # This is a heuristic and might need adjustment.
        if result["sentiment"]["confidence"] < 0.9:
             print("\nEnhanced mode handler test completed, likely with fallback as expected.")
        else:
             print("\nEnhanced mode handler test completed.")


if __name__ == '__main__':
    unittest.main()
