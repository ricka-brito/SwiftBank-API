from rest_framework import (
    viewsets, 
    status
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt import authentication as authenticationJWT
from core.models import Account, Transaction
from api import serializers
import random, decimal
from rest_framework.exceptions import PermissionDenied
from datetime import timedelta
from django.utils import timezone

from rest_framework.decorators import action

class AccountViewSet(viewsets.ViewSet):
    # "SELECT * FROM contas";
    queryset = Account.objects.all()
    authentication_classes = [authenticationJWT.JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    # def get_queryset(self):
    #     """Get account for authenticated users"""
    #     if self.request.user.id is not None:
    #         if not self.request.user.created_at + timedelta(minutes=5) <= timezone.now():
    #             raise PermissionDenied(detail="The user is still in analysis", code=status.HTTP_403_FORBIDDEN)
    #     else:
    #         raise PermissionDenied(detail='Not authenticated', code=status.HTTP_403_FORBIDDEN)
    #     queryset = self.queryset
    #     return queryset.filter(
    #         user=self.request.user
    #     ).order_by('-id').distinct()
    # # "SELECT * FROM contas where user_id = 1;"; 
    
    @action(detail=False, methods=['get'])
    def me(self, request, pk=None):
        if self.request.user.id is not None:
            if not self.request.user.created_at + timedelta(minutes=5) <= timezone.now():
                raise PermissionDenied(detail="The user is still in analysis", code=status.HTTP_403_FORBIDDEN)
        else:
            raise PermissionDenied(detail='Not authenticated', code=status.HTTP_403_FORBIDDEN)
        
        me_account = request.user.account.id
        account_object = Account.objects.get(id=me_account)
        account_serializer = serializers.AccountDetailSerializer(account_object)
        return Response(account_serializer.data)
        
            
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.AccountDetailSerializer
        elif self.action == "withdraw":
            return serializers.WithdrawSerializer
        elif self.action == "deposit":
            return serializers.WithdrawSerializer
        elif self.action == "transfer":
            return serializers.TransactionAddSerializer
        
        return serializers.AccountSerializer


    # def create(self, request, *args, **kwargs):
    #     serializer = serializers.AccountSerializer(data=request.data)
    #     if serializer.is_valid():
    #         agency = '0001'
    #         number = ''
    #         for n in range(8):
    #             number += str(random.randint(0, 9))
                
    #         account = Account(
    #             user=self.request.user,
    #             number=number,
    #             agency=agency
    #         )
            
    #         account.balance = decimal.Decimal(0)
            
    #         account.save()
            
    #         return Response({'message': 'Created'}, status=status.HTTP_201_CREATED)
        
    @action(methods=['POST'], detail=False, url_path="withdraw")
    def withdraw(self, request, pk=None):
        if request.user.id is not None:
            if not self.request.user.created_at + timedelta(minutes=5) <= timezone.now():
                raise PermissionDenied(detail="The user is still in analysis", code=status.HTTP_403_FORBIDDEN)
        else:
            raise PermissionDenied(detail='Not authenticated', code=status.HTTP_403_FORBIDDEN)
        account = Account.objects.filter(pk=self.request.user.id).first()
        
        serializers_received = serializers.WithdrawSerializer(data=request.data)
        
        if serializers_received.is_valid() and account:
            withdraw_amount = decimal.Decimal(serializers_received.validated_data.get('value'))
            balance = decimal.Decimal(account.balance)
            
            comparison = balance.compare(withdraw_amount)
            
            if comparison == 0 or comparison == 1:
                new_balance = 0 if balance - withdraw_amount <= 0 else balance - withdraw_amount
                
                account.balance = new_balance
                
                account.save()
                
                return Response({"balance": account.balance}, status=status.HTTP_200_OK)
            
            return Response({'message': 'insufficient funds'}, status=status.HTTP_403_FORBIDDEN)
        
        return Response(serializers_received.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    @action(methods=['POST'], detail=False, url_path="deposit")
    def deposit(self, request, pk=None):
        if request.user.id is not None:
            if not self.request.user.created_at + timedelta(minutes=5) <= timezone.now():
                raise PermissionDenied(detail="The user is still in analysis", code=status.HTTP_403_FORBIDDEN)
        else:
            raise PermissionDenied(detail='Not authenticated', code=status.HTTP_403_FORBIDDEN)
        account = Account.objects.filter(pk=self.request.user.id).first()
        
        serializers_received = serializers.DepositSerializer(data=request.data)
        
        if serializers_received.is_valid() and account:
            balance = decimal.Decimal(account.balance)
            deposit_amount = decimal.Decimal(serializers_received.validated_data.get('value'))
            
            account.balance = balance + deposit_amount
            account.save()
            
            return Response({"balance": account.balance}, status=status.HTTP_200_OK)

        
        return Response(serializers_received.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=False, url_path="transfer")
    def transfer(self, request, pk=None):
        if request.user.id is not None:
            if self.request.user.created_at + timedelta(minutes=5) <= timezone.now():
                sender = request.user.account.id
            else:
                raise PermissionDenied(detail="The user is still in analysis", code=status.HTTP_403_FORBIDDEN)
        else:
            raise PermissionDenied(detail='Not authenticated', code=status.HTTP_403_FORBIDDEN)
        receiver = request.data.get("receiver")
        value = request.data.get("value")
        description = request.data.get("description")
        
        if not decimal.Decimal(value).compare(0) >= 0:
            # If trys to transfer <=0
            return Response({'message': 'Invalid value for transfer'}, status=status.HTTP_403_FORBIDDEN)
        
        elif Account.objects.get(id=sender).balance.compare(decimal.Decimal(value)) == -1:
            # if there is no balance enough
            return Response({'message': 'No balance enough'}, status=status.HTTP_403_FORBIDDEN)
        
        else:
            if not Account.objects.get(id=receiver).created_at + timedelta(minutes=5) <= timezone.now():
                raise PermissionDenied(detail="The receiver is still in analysis", code=status.HTTP_403_FORBIDDEN)
            
            if sender == receiver:
                raise PermissionDenied(detail="The receiver and sender cannot be the same", code=status.HTTP_403_FORBIDDEN)
            
            transaction_serializer = serializers.TransactionSerializer(
                data={
                    "sender": sender,
                    "receiver": receiver,
                    "value": value,
                    "description": description
                }
            )
            transaction_serializer.is_valid(raise_exception=True)
            transaction_serializer.save()
            
            account_sender = Account.objects.get(id=sender)
            sender_balance = decimal.Decimal(account_sender.balance)
            account_sender.balance = sender_balance - decimal.Decimal(value)
            account_sender.save()
            
            
            account_receiver = Account.objects.get(id=receiver)
            receiver_balance = decimal.Decimal(account_receiver.balance)
            account_receiver.balance = receiver_balance + decimal.Decimal(value)
            account_receiver.save()


            return Response({'message': 'Transfered'}, status=status.HTTP_200_OK)

# class TrasactionViewSet(viewsets.GenericViewSet):
#     queryset = Transaction.objects.all()
#     # serializer_class = serializers.TransactionDetailSerializer
    
#     def get_serializer_class(self):
#         if self.action == 'retrieve':
#             return serializers.TransactionDetailSerializer
#         return serializers.TransactionAddSerializer
    
#     def create(self, request):
#         if request.user.id is not None:
#             if self.request.user.created_at + timedelta(minutes=5) <= timezone.now():
#                 sender = request.user.account.id
#             else:
#                 raise PermissionDenied(detail="The user is still in analysis", code=status.HTTP_403_FORBIDDEN)
#         else:
#             raise PermissionDenied(detail='Not authenticated', code=status.HTTP_403_FORBIDDEN)
#         receiver = request.data.get("receiver")
#         value = request.data.get("value")
#         description = request.data.get("description")
        
#         if not decimal.Decimal(value).compare(0) >= 0:
#             # If trys to transfer <=0
#             return Response({'message': 'Invalid value for transfer'}, status=status.HTTP_403_FORBIDDEN)
        
#         elif Account.objects.get(id=sender).balance.compare(decimal.Decimal(value)) == -1:
#             # if there is no balance enough
#             return Response({'message': 'No balance enough'}, status=status.HTTP_403_FORBIDDEN)
        
#         else:
#             if not Account.objects.get(id=receiver).created_at + timedelta(minutes=5) <= timezone.now():
#                 raise PermissionDenied(detail="The receiver is still in analysis", code=status.HTTP_403_FORBIDDEN)
            
#             transaction_serializer = serializers.TransactionSerializer(
#                 data={
#                     "sender": sender,
#                     "receiver": receiver,
#                     "value": value,
#                     "description": description
#                 }
#             )
#             transaction_serializer.is_valid(raise_exception=True)
#             transaction_serializer.save()
            
#             account_sender = Account.objects.get(id=sender)
#             sender_balance = decimal.Decimal(account_sender.balance)
#             account_sender.balance = sender_balance - decimal.Decimal(value)
#             account_sender.save()
            
            
#             account_receiver = Account.objects.get(id=receiver)
#             receiver_balance = decimal.Decimal(account_receiver.balance)
#             account_receiver.balance = receiver_balance + decimal.Decimal(value)
#             account_receiver.save()


#             return Response({'message': 'Transfered'}, status=status.HTTP_200_OK)