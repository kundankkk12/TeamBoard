from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Company, KBEntry, QueryLog


class TeamBoardApiTests(APITestCase):
	def create_user_with_company(self, username, password, company_name, role=Company.Role.CLIENT):
		user = User.objects.create_user(username=username, password=password, email=f'{username}@example.com')
		company = user.company
		company.company_name = company_name
		company.role = role
		company.save()
		return user

	def authenticate_client(self, username, password):
		response = self.client.post('/api/auth/login/', {
			'username': username,
			'password': password,
		}, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		token = response.data['access']
		self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

	def test_register_creates_user_company_and_returns_access_and_api_key(self):
		response = self.client.post('/api/auth/register/', {
			'username': 'acmecorp',
			'password': 'securepass123',
			'company_name': 'Acme Corp',
			'email': 'dev@acmecorp.com',
		}, format='json')

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertIn('access', response.data)
		self.assertIn('api_key', response.data)

		user = User.objects.get(username='acmecorp')
		company = user.company
		self.assertEqual(company.company_name, 'Acme Corp')
		self.assertEqual(company.role, Company.Role.CLIENT)
		self.assertTrue(company.api_key)

	def test_register_duplicate_username_returns_400(self):
		self.create_user_with_company('acmecorp', 'securepass123', 'Acme Corp')
		response = self.client.post('/api/auth/register/', {
			'username': 'acmecorp',
			'password': 'securepass123',
			'company_name': 'Acme Corp',
			'email': 'dev@acmecorp.com',
		}, format='json')

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(response.data.get('error'), 'Username already exists')

	def test_login_returns_access_company_name_and_api_key(self):
		self.create_user_with_company('acmecorp', 'securepass123', 'Acme Corp')

		response = self.client.post('/api/auth/login/', {
			'username': 'acmecorp',
			'password': 'securepass123',
		}, format='json')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('access', response.data)
		self.assertEqual(response.data['company_name'], 'Acme Corp')
		self.assertTrue(response.data['api_key'])

	def test_login_invalid_credentials_returns_401(self):
		self.create_user_with_company('acmecorp', 'securepass123', 'Acme Corp')

		response = self.client.post('/api/auth/login/', {
			'username': 'acmecorp',
			'password': 'wrong-password',
		}, format='json')

		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
		self.assertEqual(response.data.get('error'), 'Invalid credentials')

	def test_kb_query_requires_token(self):
		response = self.client.post('/api/kb/query/', {'search': 'django'}, format='json')
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_kb_query_blank_search_returns_400(self):
		self.create_user_with_company('acmecorp', 'securepass123', 'Acme Corp')
		self.authenticate_client('acmecorp', 'securepass123')

		response = self.client.post('/api/kb/query/', {'search': '   '}, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_kb_query_searches_and_logs(self):
		self.create_user_with_company('acmecorp', 'securepass123', 'Acme Corp')
		self.authenticate_client('acmecorp', 'securepass123')

		KBEntry.objects.create(
			question='What is select_related in Django ORM?',
			answer='select_related performs a SQL JOIN and fetches related objects.',
			category=KBEntry.Category.DATABASE,
		)
		KBEntry.objects.create(
			question='How does transaction.atomic() work?',
			answer='transaction.atomic wraps operations in a transaction.',
			category=KBEntry.Category.FRAMEWORK,
		)

		response = self.client.post('/api/kb/query/', {'search': 'select_related'}, format='json')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['count'], 1)
		self.assertEqual(len(response.data['results']), 1)

		log = QueryLog.objects.get(search_term='select_related')
		self.assertEqual(log.results_count, 1)
		self.assertEqual(log.company.company_name, 'Acme Corp')

	def test_kb_query_no_matches_returns_empty_and_still_logs(self):
		self.create_user_with_company('acmecorp', 'securepass123', 'Acme Corp')
		self.authenticate_client('acmecorp', 'securepass123')

		response = self.client.post('/api/kb/query/', {'search': 'no-such-term'}, format='json')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['count'], 0)
		self.assertEqual(response.data['results'], [])
		self.assertTrue(QueryLog.objects.filter(search_term='no-such-term', results_count=0).exists())

	def test_usage_summary_client_forbidden(self):
		self.create_user_with_company('acmecorp', 'securepass123', 'Acme Corp', role=Company.Role.CLIENT)
		self.authenticate_client('acmecorp', 'securepass123')

		response = self.client.get('/api/admin/usage-summary/')
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_usage_summary_admin_success(self):
		admin_user = self.create_user_with_company('admincorp', 'securepass123', 'Admin Corp', role=Company.Role.ADMIN)
		client_user = self.create_user_with_company('acmecorp', 'securepass123', 'Acme Corp', role=Company.Role.CLIENT)

		QueryLog.objects.create(company=admin_user.company, search_term='select_related', results_count=2)
		QueryLog.objects.create(company=admin_user.company, search_term='select_related', results_count=1)
		QueryLog.objects.create(company=client_user.company, search_term='jwt authentication', results_count=3)

		self.authenticate_client('admincorp', 'securepass123')
		response = self.client.get('/api/admin/usage-summary/')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['total_queries'], 3)
		self.assertEqual(response.data['active_companies'], 2)
		self.assertEqual(response.data['top_search_terms'][0]['search_term'], 'select_related')
		self.assertEqual(response.data['top_search_terms'][0]['count'], 2)
