# -*- coding: UTF-8 -*-

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from tt.models import Evento, Usuario, Categoria, Pedido, Item, Endereco
from tt.views import UsuarioAlteracaoForm, UsuarioCadastroForm


class EventoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'is_active', )
    list_display_links = ('nome',)
    list_filter = ('is_active',)
    prepopulated_fields = {'slug': ('nome',)}
    search_fields = ('nome', 'descricao')

class EnderecoInLine(admin.TabularInline):
    model = Endereco
    readonly_fields = ('cidade', 'estado', 'logradouro', 'cep', 'nro', 'complemento', 'padrao',)
    extra = 0
    max_num = 0
    can_delete = False

class UsuarioAdmin(UserAdmin):
    # The forms to add and change user instances
    form = UsuarioAlteracaoForm
    add_form = UsuarioCadastroForm

    def get_form(self, request, obj=None, **kwargs):
        if obj:
            # change page
            self.readonly_fields = ['username', 'email', 'data_nascimento', 'nome', 'cpf', 'telefone']
            self.inlines = (EnderecoInLine,)
        else:
            # add page
            self.inlines = ()
        return super(UsuarioAdmin, self).get_form(request, obj, **kwargs)

    def add_view(self, request, form_url="", extra_context=None):
        data = request.GET.copy()
        data['is_admin'] = True
        request.GET = data
        return super(UsuarioAdmin, self).add_view(request, form_url="", extra_context=extra_context)

    list_display = ('username', 'is_admin', 'is_active', 'email', 'data_nascimento',)
    list_display_links = ('username', 'email')
    list_filter = ('email', 'username',)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'cpf', 'telefone')}),
        ('Dados pessoais', {'fields': ('nome', 'data_nascimento',)}),
        #('Permissions', {'fields': ('is_admin',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'data_nascimento', 'password1', 'password2', 'is_admin')}
        ),
    )

    search_fields = ('email', 'username',)
    ordering = ('is_active', 'username')
    filter_horizontal = ()

    def render_change_form(self, request, context, *args, **kwargs):
        def get_queryset(original_func):
            import inspect, itertools
            def wrapped_func():
                if inspect.stack()[1][3] == '__iter__':
                    return itertools.repeat(None)
                return original_func()
            return wrapped_func

        for formset in context['inline_admin_formsets']:
            formset.formset.get_queryset = get_queryset(formset.formset.get_queryset)

        return super(UsuarioAdmin, self).render_change_form(request, context,*args, **kwargs)

class ItemInLine(admin.TabularInline):
    model = Item
    readonly_fields = ('evento', 'quantidade', 'subtotal',)
    fields = ('evento', 'quantidade', 'subtotal',)
    extra = 0
    max_num = 0
    can_delete = False

class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'data_criado', 'status')
    readonly_fields = ('data_criado', 'user', 'total', 'id',)
    fields = ('id', 'status', 'data_criado', 'user', 'total', )
    inlines = (ItemInLine,)
    can_delete = False
    search_fields = ['id']

    # pra não exibir a string que representa o objeto a cada linha,
    # o jeito mais fácil sem alterar templates do djago... porque inventaram isso?
    def render_change_form(self, request, context, *args, **kwargs):
        def get_queryset(original_func):
            import inspect, itertools
            def wrapped_func():
                if inspect.stack()[1][3] == '__iter__':
                    return itertools.repeat(None)
                return original_func()
            return wrapped_func

        for formset in context['inline_admin_formsets']:
            formset.formset.get_queryset = get_queryset(formset.formset.get_queryset)

        return super(PedidoAdmin, self).render_change_form(request, context,*args, **kwargs)

admin.site.register(Pedido, PedidoAdmin)
admin.site.register(Categoria)
admin.site.register(Evento, EventoAdmin)
admin.site.register(Usuario, UsuarioAdmin)

admin.site.unregister(Group)