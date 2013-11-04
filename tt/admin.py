# -*- coding: UTF-8 -*-

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from tt.models import Evento, Usuario, Categoria, Pedido, Item
from tt.views import UsuarioCadastroForm, UsuarioAlteracaoForm


class EventoAdmin(admin.ModelAdmin):
    list_display = ('is_active', 'nome')
    list_display_links = ('nome',)
    list_filter = ('is_active',)
    prepopulated_fields = {'slug': ('nome',)}
    search_fields = ('nome', 'descricao')

class UsuarioAdmin(UserAdmin):
    # The forms to add and change user instances
    form = UsuarioAlteracaoForm
    add_form = UsuarioCadastroForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'data_nascimento',)
    list_filter = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('data_nascimento',)}),
        #('Permissions', {'fields': ('is_admin',)}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'data_nascimento', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()

class PedidoAdmin(admin.ModelAdmin):
    readonly_fields = ('data_criado', 'user', 'total',)

    fields = ('status', 'data_criado', 'user', 'total',)

admin.site.register(Pedido, PedidoAdmin)
admin.site.register(Categoria)
admin.site.register(Evento, EventoAdmin)
admin.site.register(Usuario, UsuarioAdmin)

admin.site.unregister(Group)