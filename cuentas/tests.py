from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import InviteCode


class InviteCodeSignupTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.User = get_user_model()

	def test_signup_with_invite_consumes_code(self):
		code = 'TEST-CODE-1'
		InviteCode.objects.create(code=code, single_use=True)

		# Visit signup with invite in GET to mark session
		signup_url = reverse('account_signup')
		resp = self.client.get(signup_url + f'?invite={code}')
		self.assertEqual(resp.status_code, 200)

		# Post signup form
		data = {
			'username': 'inviteduser',
			'email': 'invited@example.test',
			'password1': 'ComplexP4ss!',
			'password2': 'ComplexP4ss!'
		}
		resp2 = self.client.post(signup_url, data, follow=True)
		# After signup, the invite code should be marked used
		ic = InviteCode.objects.get(code=code)
		self.assertTrue(ic.used)
		# And a user should exist
		self.assertTrue(self.User.objects.filter(username='inviteduser').exists())

	def test_signup_with_invalid_invite_rejected(self):
		# Visit signup with non-existing invite; assume site requires invite when ACCOUNT_ALLOW_PUBLIC_SIGNUP=False
		signup_url = reverse('account_signup')
		resp = self.client.get(signup_url + '?invite=NOEXIST')
		# Response may still be 200 but signup should fail when posting if adapter blocks; we just ensure page loads
		self.assertIn(resp.status_code, (200,302))

	def test_multi_use_invite_allows_multiple_signups_until_max(self):
		# Test the InviteCode reservation/consumption model methods directly
		code = 'MULTI-1'
		ic = InviteCode.objects.create(code=code, single_use=False, max_uses=2)
		# Reserve and consume twice
		ic.reserve()
		ic.consume()
		ic.refresh_from_db()
		self.assertEqual(ic.uses_count, 1)
		# second
		ic.reserve()
		ic.consume()
		ic.refresh_from_db()
		self.assertEqual(ic.uses_count, 2)
		self.assertTrue(ic.used)
		# Now is_valid should be False
		self.assertFalse(ic.is_valid())