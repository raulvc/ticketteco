# -*- coding: UTF-8 -*-

from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from tt.models import Usuario, Endereco


class EventoDetalheForm(forms.Form):
    quantidade = forms.IntegerField(label='quantidade', initial=1, min_value=1, max_value=100)
    def clean(self):
        super(EventoDetalheForm, self).clean()
        qtd = self.cleaned_data.get('quantidade')
        # as duas senhas tem que ser iguais
        if qtd > 5:
            raise forms.ValidationError('Limite de 5 tickets por usuário.')
        return self.cleaned_data

class UsuarioCadastroForm(forms.ModelForm):
    password1 = forms.CharField(max_length=20, required=True, widget=forms.PasswordInput(), label="Senha")
    password2 = forms.CharField(max_length=20, required=True, widget=forms.PasswordInput(), label="Repita a senha")
    email = forms.EmailField(widget=forms.TextInput(attrs={'autofocus': 'autofocus'}))

    class Meta:
        model = Usuario
        fields = ['email', 'nome', 'data_nascimento', 'cpf', 'telefone', 'username']

    def clean(self):
        super(UsuarioCadastroForm, self).clean()
        password1 = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        # as duas senhas tem que ser iguais
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Senhas não correspondem.')
        return self.cleaned_data

    def save(self, commit=True):
        novo_usuario = super(UsuarioCadastroForm, self).save(commit=False)
        novo_usuario.set_password(self.cleaned_data['password1'])
        if commit:
            novo_usuario.save()
        return novo_usuario

class UsuarioAlteracaoForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = Usuario
        fields = ['email', 'nome', 'data_nascimento', 'cpf', 'telefone', 'username']

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]

class EnderecoCadastroForm(forms.ModelForm):
    class Meta:
        model = Endereco
        fields = ['logradouro', 'nro', 'complemento', 'cidade', 'estado', 'cep']