from rest_framework import (
    viewsets, 
    status
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt import authentication as authenticationJWT
from core.models import Account
from api import serializers
import random, decimal

from rest_framework.decorators import action

class AccountViewSet(viewsets.ModelViewSet):
    # "SELECT * FROM contas";
    queryset = Account.objects.all()
    authentication_classes = [authenticationJWT.JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get account for authenticated users"""
        queryset = self.queryset
        return queryset.filter(
            user=self.request.user
        ).order_by('-id').distinct()
    # "SELECT * FROM contas where user_id = 1;"; 
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.AccountDetailSerializer
        
        return serializers.AccountSerializer

    
    def create(self, request, *args, **kwargs):
        serializer = serializers.AccountSerializer(data=request.data)
        if serializer.is_valid():
            agency = '0001'
            number = ''
            for n in range(8):
                number += str(random.randint(0, 9))
                
            account = Account(
                user=self.request.user,
                number=number,
                agency=agency
            )
            
            account.balance = decimal.Decimal(0)
            
            account.save()
            
            return Response({'message': 'Created'}, status=status.HTTP_201_CREATED)
        
    @action(methods=['POST'], detail=True, url_path="withdraw")
    def withdraw(self, request, pk=None):
        account = Account.objects.filter(id=pk).first()
        
        serializers_received = serializers.WithdrawSerializer(request=request.data)
        
        if serializers_received.is_valid() and account:
            withdraw_amount = decimal.Decimal(serializers_received.validated_data.get('value'))
            balance = decimal.Decimal(account.balance)
            
            comparison = balance.compare(withdraw_amount)
            
            if comparison == 0 or comparison == 1:
                new_balance = 0 if balance - withdraw_amount <= 0 else balance - withdraw_amount
                
                account.balance = new_balance
                
                account.save()
                
                return Response({"saldo": account.balance}, status=status.HTTP_200_OK)
            
            return Response({'message': 'insufficient funds'}, status=status.HTTP_403_FORBIDDEN)
        
        return Response(serializers_received.errors, status=status.HTTP_400_BAD_REQUEST)