import datetime
from multiprocessing.sharedctypes import Value
import re
from rest_framework import (
    viewsets, 
    status
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt import authentication as authenticationJWT
from core.models import Account, Transaction, LoanInstallments, Loan
from api import serializers
import random, decimal
from rest_framework.exceptions import PermissionDenied, NotFound
from datetime import timedelta
from django.utils import timezone
from rest_framework.decorators import action
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
import math;
from dateutil.relativedelta import relativedelta

class CustomPagination(PageNumberPagination):
    page_size = 10  # Set your desired page size here
    page_size_query_param = 'limit'
    max_page_size = 1000  # Set your maximum page size here

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'results': data
        })

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
        account = Account.objects.filter(pk=self.request.user.account.id).first()
        
        serializers_received = serializers.WithdrawSerializer(data=request.data)
        
        if serializers_received.is_valid() and account:
            withdraw_amount = decimal.Decimal(serializers_received.validated_data.get('value'))
            balance = decimal.Decimal(account.balance)
            
            comparison = balance.compare(withdraw_amount)
            
            if comparison == 0 or comparison == 1:
                new_balance = 0 if balance - withdraw_amount <= 0 else balance - withdraw_amount
                
                account.balance = new_balance
                
                account.save()
                
                transaction_serializer = serializers.TransactionSerializer(
                    data={
                        "sender": self.request.user.id,
                        "receiver": self.request.user.id,
                        "value": withdraw_amount,
                        "transaction_type": Transaction.TransactionTypes.WITHDRAW
                    }
                )
                transaction_serializer.is_valid(raise_exception=True)
                transaction_serializer.save()
                
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
        account = Account.objects.filter(pk=self.request.user.account.id).first()
        
        serializers_received = serializers.DepositSerializer(data=request.data)
        
        if serializers_received.is_valid() and account:
            balance = decimal.Decimal(account.balance)
            deposit_amount = decimal.Decimal(serializers_received.validated_data.get('value'))
            
            account.balance = balance + deposit_amount
            account.save()
            
            transaction_serializer = serializers.TransactionSerializer(
                data={
                    "sender": self.request.user.id,
                    "receiver": self.request.user.id,
                    "value": deposit_amount,
                    "transaction_type": Transaction.TransactionTypes.DEPOSIT
                }
            )
            transaction_serializer.is_valid(raise_exception=True)
            transaction_serializer.save()
                
            
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
                    "description": description,
                    "transaction_type": Transaction.TransactionTypes.TRANSFER
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
          
    @extend_schema(
        parameters=[
            OpenApiParameter("page", OpenApiTypes.INT, OpenApiParameter.QUERY),
            OpenApiParameter("limit", OpenApiTypes.INT, OpenApiParameter.QUERY),
        ],
    )   
    @action(methods=['GET'], detail=False, url_path="statement")
    def statement(self, request, pk=None):
        if request.user.id is not None:
            if self.request.user.created_at + timedelta(minutes=5) <= timezone.now():
                user = request.user.account.id
            else:
                raise PermissionDenied(detail="The user is still in analysis", code=status.HTTP_403_FORBIDDEN)
        else:
            raise PermissionDenied(detail='Not authenticated', code=status.HTTP_403_FORBIDDEN)
        
        queryset = Transaction.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).order_by('-created_at')
        serializer = serializers.TransactionDetailSerializer(queryset, many=True)

        
        paginator = CustomPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        serializer = serializers.TransactionDetailSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @action(methods=['GET'], detail=False, url_path="transaction/(?P<pk>[^/.]+)")
    def transaction(self, request, pk):
        if request.user.id is not None:
            if self.request.user.created_at + timedelta(minutes=5) <= timezone.now():
                user = request.user.account.id
            else:
                raise PermissionDenied(detail="The user is still in analysis", code=status.HTTP_403_FORBIDDEN)
        else:
            raise PermissionDenied(detail='Not authenticated', code=status.HTTP_403_FORBIDDEN)
        
        try:
            transaction = Transaction.objects.get(
                Q(sender=user) | Q(receiver=user),
                id=pk
            )
            
            serializer = serializers.TransactionDetailSerializer(transaction)
            return Response(serializer.data)
            
        except Transaction.DoesNotExist:
            raise NotFound(detail='Transaction not found', code=status.HTTP_404_NOT_FOUND)



class LoanViewSet(viewsets.ViewSet):
    # "SELECT * FROM contas";
    queryset = Loan.objects.all()
    authentication_classes = [authenticationJWT.JWTAuthentication]
    permission_classes = [IsAuthenticated]


    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.LoanSerializer
        if self.action == 'conditions':
            return serializers.LoanSerializer


    # @action(methods=['POST'], detail=False, url_path="loan")
    def create(self, request, pk=None):
        if request.user.id is not None:
            if not self.request.user.created_at + timedelta(minutes=5) <= timezone.now():
                raise PermissionDenied(detail="The user is still in analysis", code=status.HTTP_403_FORBIDDEN)
        else:
            raise PermissionDenied(detail='Not authenticated', code=status.HTTP_403_FORBIDDEN)
        account = Account.objects.filter(pk=self.request.user.account.id).first()

        serializers_received = serializers.LoanSerializer(data=request.data)
        if serializers_received.is_valid() and account:
            installment = serializers_received.validated_data.get('installments')
            request_amount = decimal.Decimal(serializers_received.validated_data.get('value'))
            
            fee = math.log((installment/float(request_amount)), installment)*(-installment/float(request_amount))*math.sqrt(float(request_amount))

            installment_price = (float(request_amount) + float(request_amount) * fee)/installment

            if installment_price > float(self.request.user.declared_salary) * 2.5:
                return Response({"Not allowed (installment too high)"}, status=status.HTTP_403_FORBIDDEN)
            
            else:
                loan = Loan(
                account=account, 
                installments=installment,
                value=request_amount,
                fees=fee
                )
                loan.save()
                
                for i in range(installment):
                    due_date = datetime.datetime.now() + relativedelta(months=+(i+1))
                    due_date = datetime.datetime.combine( due_date , datetime.datetime.min.time())
                    loanInstallment = LoanInstallments(
                        loan=loan,
                        value=installment_price,
                        due_date=due_date.replace(day=15)
                    )
                    loanInstallment.save()
                    
                account_sender = Account.objects.get(id=request.user.account.id)
                sender_balance = decimal.Decimal(account_sender.balance)
                account_sender.balance = sender_balance + decimal.Decimal(request_amount)
                account_sender.save()
            
                
                return Response({"loan requested"}, status=status.HTTP_200_OK)

                
        
        return Response(serializers_received.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=False, url_path="conditions")
    def conditions(self, request, pk=None):
        if request.user.id is not None:
            if not self.request.user.created_at + timedelta(minutes=5) <= timezone.now():
                raise PermissionDenied(detail="The user is still in analysis", code=status.HTTP_403_FORBIDDEN)
        else:
            raise PermissionDenied(detail='Not authenticated', code=status.HTTP_403_FORBIDDEN)
        account = Account.objects.filter(pk=self.request.user.account.id).first()

        serializers_received = serializers.LoanSerializer(data=request.data)
        if serializers_received.is_valid() and account:
            installment = serializers_received.validated_data.get('installments')
            request_amount = decimal.Decimal(serializers_received.validated_data.get('value'))
            
            fee = math.log((installment/float(request_amount)), installment)*(-installment/float(request_amount))*math.sqrt(float(request_amount))

            installment_price = (float(request_amount) + float(request_amount) * fee)/installment
            
            return Response({"loan_info": {"installments": installment, "request_amount": request_amount, "fee": round(fee, 2), "total": round(float(request_amount) + float(request_amount) * fee, 2), "installment_price" : round(installment_price, 2), "max_installment_value": float(self.request.user.declared_salary) * 2.5}}, status=status.HTTP_200_OK)
        
        return Response(serializers_received.errors, status=status.HTTP_400_BAD_REQUEST)
        
        
    @extend_schema(
    parameters=[
        OpenApiParameter("page", OpenApiTypes.INT, OpenApiParameter.QUERY),
        OpenApiParameter("limit", OpenApiTypes.INT, OpenApiParameter.QUERY),
        OpenApiParameter("payed", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
    ],
    )   
    @action(methods=['GET'], detail=False, url_path="statement")
    def statement(self, request, pk=None):
        if request.user.id is not None:
            if self.request.user.created_at + timedelta(minutes=5) <= timezone.now():
                user = request.user.account.id
            else:
                raise PermissionDenied(detail="The user is still in analysis", code=status.HTTP_403_FORBIDDEN)
        else:
            raise PermissionDenied(detail='Not authenticated', code=status.HTTP_403_FORBIDDEN)
        
        payed = self.request.query_params.get('payed')
        
        print(payed)
        
        if payed == "true":
            queryset = Loan.objects.filter(Q(account=user), payed=True).order_by('-request_date')
        
        else:
            queryset = Loan.objects.filter(Q(account=user)).order_by('-request_date')
        
        serializer = serializers.LoanSerializer(queryset, many=True)

        
        paginator = CustomPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        serializer = serializers.LoanSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @action(methods=['GET'], detail=False, url_path="statement/(?P<pk>[^/.]+)")
    def loan(self, request, pk):
        if request.user.id is not None:
            if self.request.user.created_at + timedelta(minutes=5) <= timezone.now():
                user = request.user.account.id
            else:
                raise PermissionDenied(detail="The user is still in analysis", code=status.HTTP_403_FORBIDDEN)
        else:
            raise PermissionDenied(detail='Not authenticated', code=status.HTTP_403_FORBIDDEN)
        
        try:
            loan = Loan.objects.get(
                Q(account=user),
                id=pk
            )
            
            serializer = serializers.LoanDetailSerializer(loan)
            return Response(serializer.data)
            
        except Transaction.DoesNotExist:
            raise NotFound(detail='Transaction not found', code=status.HTTP_404_NOT_FOUND)
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