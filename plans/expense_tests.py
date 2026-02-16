from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from plans.models import Plan, PlanMember
from plans.expense_models import Expense, ExpenseShare

class ExpenseModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='u1', email='u1@example.com', password='pw')
        self.user2 = User.objects.create_user(username='u2', email='u2@example.com', password='pw')
        self.plan = Plan.objects.create(title='Test Plan', category='travel', creator=self.user1)
        self.member1 = PlanMember.objects.create(plan=self.plan, user=self.user1, role='creator', status='active', invited_by=self.user1)
        self.member2 = PlanMember.objects.create(plan=self.plan, user=self.user2, role='member', status='active', invited_by=self.user1)

    def test_expense_equal_split(self):
        expense = Expense.objects.create(plan=self.plan, description='Dinner', amount=100, category='food', paid_by=self.user1, split_method='equal')
        share1 = ExpenseShare.objects.create(expense=expense, member=self.member1, amount=50)
        share2 = ExpenseShare.objects.create(expense=expense, member=self.member2, amount=50)
        self.assertEqual(share1.amount, 50)
        self.assertEqual(share2.amount, 50)
        self.assertFalse(share1.is_settled)
        self.assertFalse(share2.is_settled)

    def test_expense_custom_split(self):
        expense = Expense.objects.create(plan=self.plan, description='Taxi', amount=60, category='transport', paid_by=self.user2, split_method='custom')
        share1 = ExpenseShare.objects.create(expense=expense, member=self.member1, amount=20)
        share2 = ExpenseShare.objects.create(expense=expense, member=self.member2, amount=40)
        self.assertEqual(share1.amount, 20)
        self.assertEqual(share2.amount, 40)

    def test_settle_share(self):
        expense = Expense.objects.create(plan=self.plan, description='Lunch', amount=40, category='food', paid_by=self.user1, split_method='equal')
        share = ExpenseShare.objects.create(expense=expense, member=self.member2, amount=20)
        share.is_settled = True
        share.save()
        self.assertTrue(ExpenseShare.objects.get(id=share.id).is_settled)

class ExpenseAPITest(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='u1', email='u1@example.com', password='pw')
        self.user2 = User.objects.create_user(username='u2', email='u2@example.com', password='pw')
        self.plan = Plan.objects.create(title='Test Plan', category='travel', creator=self.user1)
        self.member1 = PlanMember.objects.create(plan=self.plan, user=self.user1, role='creator', status='active', invited_by=self.user1)
        self.member2 = PlanMember.objects.create(plan=self.plan, user=self.user2, role='member', status='active', invited_by=self.user1)
        self.client.force_authenticate(user=self.user1)

    def test_add_expense_equal(self):
        data = {
            'plan': str(self.plan.id),
            'description': 'Dinner',
            'amount': 100,
            'category': 'food',
            'paid_by': self.user1.id,
            'split_method': 'equal',
        }
        response = self.client.post('/api/expenses/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['description'], 'Dinner')
        self.assertEqual(response.data['split_method'], 'equal')

    def test_add_expense_custom(self):
        data = {
            'plan': str(self.plan.id),
            'description': 'Taxi',
            'amount': 60,
            'category': 'transport',
            'paid_by': self.user2.id,
            'split_method': 'custom',
            'shares': [
                {'member': str(self.member1.id), 'amount': 20},
                {'member': str(self.member2.id), 'amount': 40},
            ]
        }
        response = self.client.post('/api/expenses/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['description'], 'Taxi')
        self.assertEqual(response.data['split_method'], 'custom')

    def test_settle_expense_share(self):
        expense = Expense.objects.create(plan=self.plan, description='Lunch', amount=40, category='food', paid_by=self.user1, split_method='equal')
        share = ExpenseShare.objects.create(expense=expense, member=self.member2, amount=20)
        url = f'/api/expenses/{expense.id}/settle/'
        response = self.client.post(url, {'member': str(self.member2.id)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        share.refresh_from_db()
        self.assertTrue(share.is_settled)
