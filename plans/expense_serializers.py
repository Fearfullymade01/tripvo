from rest_framework import serializers
from django.contrib.auth.models import User
from .models import PlanMember
from .expense_models import Expense, ExpenseShare

class ExpenseShareSerializer(serializers.ModelSerializer):
    member_name = serializers.SerializerMethodField()
    class Meta:
        model = ExpenseShare
        fields = ['id', 'member', 'member_name', 'amount', 'is_settled', 'settled_at']
        read_only_fields = ['id', 'member_name']
    def get_member_name(self, obj):
        if obj.member.user:
            return obj.member.user.get_full_name() or obj.member.user.username
        return obj.member.guest_name or obj.member.guest_email

class ExpenseSerializer(serializers.ModelSerializer):
    paid_by_info = serializers.SerializerMethodField()
    shares = ExpenseShareSerializer(many=True, read_only=True)
    class Meta:
        model = Expense
        fields = [
            'id', 'plan', 'description', 'amount', 'category', 'paid_by', 'paid_by_info',
            'split_method', 'created_at', 'updated_at', 'shares'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'shares', 'paid_by_info']
    def get_paid_by_info(self, obj):
        return {
            'id': obj.paid_by.id,
            'username': obj.paid_by.username,
            'email': obj.paid_by.email
        }
