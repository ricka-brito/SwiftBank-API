from rest_framework import serializers
from core.models import Account, Transaction, Loan, LoanInstallments

class AccountSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Account
        fields = ['agency', 'number']
        read_only_fields = ['number']


class AccountDetailSerializer(AccountSerializer):
    class Meta(AccountSerializer.Meta):
        fields = AccountSerializer.Meta.fields + ['id', 'balance', 'created_at']
        read_only_fields = AccountSerializer.Meta.read_only_fields + ['id', 'balance', 'created_at']
        
class TransactionSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(),
        many=False
    )
    receiver = serializers.PrimaryKeyRelatedField(
    queryset=Account.objects.all(),
    many=False
    )
    
    class Meta:
        model = Transaction
        fields = ['id', 'sender', 'receiver', 'value', 'description', 'transaction_type']
        read_only_fields = ['id']


class TransactionDetailSerializer(serializers.ModelSerializer):
    sender = AccountSerializer()
    receiver = AccountSerializer()
    
    class Meta:
        model = Transaction
        fields = ['id', 'sender', 'receiver', 'value', 'description', 'transaction_type', 'created_at']
        read_only_fields = ['id', 'sender', 'created_at']

class TransactionAddSerializer(serializers.ModelSerializer):
    receiver = serializers.PrimaryKeyRelatedField(
    queryset=Account.objects.all(),
    many=False
    )
    
    class Meta:
        model = Transaction
        fields = ['id', 'sender', 'receiver', 'value', 'description']
        read_only_fields = ['id', 'sender']


class DepositSerializer(serializers.Serializer):
    value = serializers.DecimalField(max_digits= 10, decimal_places=2, min_value=1)

    class Meta:
        fields = ['value']


class WithdrawSerializer(serializers.Serializer):
    value = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=1)

    class Meta:
        fields = ['value']
    
class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ['installments','value', 'request_date', 'payed']
        

class LoanInstallmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanInstallments
        fields = ['id', 'payed_date', 'due_date', 'value']
        
class LoanDetailSerializer(serializers.ModelSerializer):
    installment = LoanInstallmentsSerializer(many=True, read_only=True)
    
    class Meta:
        model = Loan
        fields = ['account', 'installments', 'request_date', 'payed', 'value', 'fees', 'installment']