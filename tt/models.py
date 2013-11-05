# -*- coding: UTF-8 -*-
from decimal import Decimal

from django.db import models
from django.utils.datetime_safe import datetime
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser


class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, unique=True)
    descricao = models.TextField(verbose_name='descrição', blank=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'categoria'
        verbose_name_plural = 'categorias'
    def __unicode__(self):
        return self.nome

class Evento(models.Model):
    is_active = models.BooleanField(default=True, verbose_name='Ativo?')

    categoria = models.ForeignKey(Categoria, related_name='eventos', blank=True, null=True)

    nome = models.CharField(max_length=255)
    descricao = models.TextField(verbose_name='descrição', blank=True)
    foto = models.ImageField(upload_to='img/eventos', blank=True)
    data = models.DateField()
    local = models.TextField()
    slug = models.SlugField(max_length=150, unique=True)
    preco = models.DecimalField(max_digits=18, decimal_places=2, verbose_name='preço unitário')

    class Meta:
        ordering = ['nome']
        verbose_name = 'evento'
        verbose_name_plural = 'eventos'

    def __unicode__(self):
        return self.nome

    @models.permalink
    def get_absolute_url(self):
        return ('detalhe_evento', (), {'evento_id': self.pk})

#class Setor(models.Model):
#    evento = models.ForeignKey('Evento', related_name='setores')
#    nome = models.CharField(max_length=300)
#    qtd_lugares = models.IntegerField()
#    preco_extra = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
#    def __unicode__(self):
#       return u'%s' % self.name

class UsuarioManager(BaseUserManager):
    def create_user(self, username, email, data_nasc, password, nome, cpf, telefone):
        if not email:
            raise ValueError('É necessário informar um e-mail')

        user = self.model(
            username=username,
            email=UsuarioManager.normalize_email(email),
            data_nascimento=data_nasc,
            nome = nome,
            cpf = cpf,
            telefone = telefone,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, username, password, email=None, data_nasc=None, nome=None, cpf=None, telefone=None):
        user = self.model(
            username=username,
            email=UsuarioManager.normalize_email(email),
            data_nascimento=data_nasc,
            nome = nome,
            cpf = cpf,
            telefone = telefone,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

class Usuario(AbstractBaseUser):
    username = models.CharField(max_length=30, unique=True, verbose_name='usuário')
    email = models.EmailField(max_length=255, verbose_name='e-mail')
    data_nascimento = models.DateField(null=True, blank=True)
    nome = models.CharField(max_length=255, null=True, blank=True)
    cpf = models.CharField(max_length=11, null=True, blank=True)
    telefone = models.CharField(max_length=30, null=True, blank=True)

    is_active = models.BooleanField(default=True, verbose_name='ativo?')
    is_admin = models.BooleanField(default=False, verbose_name='administrador?')

    objects = UsuarioManager()

    USERNAME_FIELD = 'username'

    def get_full_name(self):
        # The user is identified by their email address
        return self.nome

    def get_short_name(self):
        # The user is identified by their email address
        return self.nome.split(' ')[0]

    def __unicode__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


class Endereco(models.Model):
    user = models.ForeignKey(Usuario, related_name='enderecos')
    cidade = models.CharField(max_length=50)
    estado = models.CharField(max_length=30)
    logradouro = models.CharField(max_length=30)
    cep = models.CharField(max_length=30)
    nro = models.IntegerField(verbose_name='número')
    complemento = models.CharField(max_length=30, blank=True, null=True)
    padrao = models.BooleanField(default=False)
    def __unicode__(self):
        return self.logradouro

class Pedido(models.Model):
    # status
    CONFIRMADO = 10
    PAGO = 20
    FINALIZADO = 30
    CANCELADO = 40
    ESCOLHAS = ((CONFIRMADO, 'Pedido foi confirmado'), (PAGO, 'Pedido foi pago'),
                (FINALIZADO, 'Pedido finalizado'), (CANCELADO, 'Pedido cancelado'))
    data_criado = models.DateTimeField(verbose_name='data do pedido', default=datetime.now)
    user = models.ForeignKey(Usuario, related_name='pedidos')
    endereco_entrega = models.ForeignKey(Endereco, related_name='+')
    status = models.PositiveIntegerField(choices=ESCOLHAS, default=CONFIRMADO)
    metodo_envio = models.CharField(verbose_name='método de envio', max_length=100)
    custo_envio = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    total = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = 'pedido'
        verbose_name_plural = 'pedidos'

    def __unicode__(self):
        return 'ID: %d' % self.pk

    def recalcula_total(self, save=True):
        items = list(self.items.all())
        for item in items:
            self.total += item.subtotal
        if self.custo_envio:
            self.total += self.custo_envio
        if save:
            self.save()

class Item(models.Model):
    evento = models.ForeignKey('Evento', blank=True, null=True, on_delete=models.SET_NULL)
    quantidade = models.IntegerField()
    pedido = models.ForeignKey('Pedido', related_name='items')

    class Meta:
        ordering = ('evento',)
        verbose_name = 'item do pedido'
        verbose_name_plural = 'itens do pedido'

    def __unicode__(self):
        return '%d lugar(es) para %s' % (self.quantidade, self.evento.nome)

    @property
    def subtotal(self):
        return self.evento.preco * self.quantidade

