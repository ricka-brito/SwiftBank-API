from rest_framework import serializers
from core.models import Account


class AccountSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Account
        fields = ['agency', 'number']
        read_only_fields = ['number']


class AccountDetailSerializer(AccountSerializer):
    class Meta(AccountSerializer.Meta):
        fields = AccountSerializer.Meta.fields + ['id', 'balance', 'created_at']
        read_only_fields = AccountSerializer.Meta.read_only_fields + ['id', 'balance', 'created_at']