from django.test import TestCase

class TimelineGameViewTest(TestCase):
    def test_redirect_if_no_access_token(self):
        response = self.client.get('/game/timeline-game/')
        self.assertEqual(response.status_code, 302)  # Redirect to Spotify login
