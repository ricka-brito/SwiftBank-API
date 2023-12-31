"""
File admin django
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _ 

from core import models

class UserAdmin(BaseUserAdmin):
    """Define the admin pages for user"""
    
    ordering = ['id']
    list_display = ['id', 'first_name', 'cpf']
    fieldsets = (
        (None, {
            "fields": (
                'email', 
                'password',
            ),
        }),
        (_('Personal info'), {"fields": ('first_name', 'cpf', 'url_imagem')}),
        (
            _('Permissions'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                )
            }
        ),
        (_('Important dates'), {'fields': ('last_login', 'created_at', )})
    )
    readonly_fields = ['last_login', 'created_at']
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'first_name',
                'email',
                'cpf',
                'url_imagem',
                'password1',
                'password2',
                'is_active',
                'is_staff',
                'is_superuser'                
            )
        }),
    )
    
admin.site.register(models.User, UserAdmin)