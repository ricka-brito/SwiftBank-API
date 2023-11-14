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


class DepositSerializer(serializers.Serializer):
    value = serializers.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        fields = ['value']


class WithdrawSerializer(serializers.Serializer):
    value = serializers.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        fields = ['value']
    