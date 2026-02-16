from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from .models import Plan, PlanMember
from .expense_models import Expense, ExpenseShare
from .expense_serializers import ExpenseSerializer, ExpenseShareSerializer
from .services import NotificationService

class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        plan_id = self.request.query_params.get('plan')
        if plan_id:
            return Expense.objects.filter(plan_id=plan_id)
        return Expense.objects.none()

    def perform_create(self, serializer):
        with transaction.atomic():
            expense = serializer.save(paid_by=self.request.user)
            plan = expense.plan
            members = PlanMember.objects.filter(plan=plan, status__in=['active', 'creator', 'admin', 'member'])
            shares = []
            if expense.split_method == 'equal':
                share_amount = expense.amount / members.count()
                for member in members:
                    shares.append(ExpenseShare(expense=expense, member=member, amount=share_amount))
            elif expense.split_method == 'custom':
                custom_shares = self.request.data.get('shares', [])
                for share in custom_shares:
                    member_id = share['member']
                    amount = share['amount']
                    member = PlanMember.objects.get(id=member_id, plan=plan)
                    shares.append(ExpenseShare(expense=expense, member=member, amount=amount))
            ExpenseShare.objects.bulk_create(shares)
            NotificationService.send_expense_notification(expense, plan, members)

    @action(detail=True, methods=['post'])
    def settle(self, request, pk=None):
        expense = self.get_object()
        member = get_object_or_404(PlanMember, id=request.data.get('member'))
        share = get_object_or_404(ExpenseShare, expense=expense, member=member)
        share.is_settled = True
        share.settled_at = timezone.now()
        share.save()
        return Response({'status': 'settled'})
