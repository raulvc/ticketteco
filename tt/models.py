# -*- coding: UTF-8 -*-
from decimal import Decimal

from django.db import models
from django.utils.datetime_safe import datetime
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from ticketteco.settings import MEDIA_URL


class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, unique=True)
    descricao = models.TextField(verbose_name='descrição', blank=True)
    foto = models.ImageField(upload_to='img/categorias', blank=True)
    thumb = models.ImageField(upload_to='img/categorias/thumb', blank=True)

    # hierarquia
    pai = models.ForeignKey('self', blank=True, null=True,
                             related_name='filhos')

    class Meta:
        ordering = ['nome']
        verbose_name = 'categoria'
        verbose_name_plural = 'categorias'

    @models.permalink
    def get_absolute_url(self):
        return ('detalhe_categoria', (), {'slug': self.slug})

    # para ser usado na interface administrativa
    def get_thumb(self):
        return '<img src="%s%s"/>' % (MEDIA_URL, self.thumb)
    get_thumb.allow_tags = True
    get_thumb.short_description = ""

    def create_thumbnail(self):
        # original code for this method came from
        # http://snipt.net/danfreak/generate-thumbnails-in-django-with-pil/

        # If there is no image associated with this.
        # do not create thumbnail
        if not self.foto:
            return

        from PIL import Image
        from cStringIO import StringIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        import os

        # Set our max thumbnail size in a tuple (max width, max height)
        THUMBNAIL_SIZE = (50, 50)

        # Open original photo which we want to thumbnail using PIL's Image
        image = Image.open(StringIO(self.foto.read()))
        image_type = image.format.lower()

        # We use our PIL Image object to create the thumbnail, which already
        # has a thumbnail() convenience method that contrains proportions.
        # Additionally, we use Image.ANTIALIAS to make the image look better.
        # Without antialiasing the image pattern artifacts may result.
        image.thumbnail(THUMBNAIL_SIZE, Image.ANTIALIAS)

        # Save the thumbnail
        temp_handle = StringIO()
        image.save(temp_handle, image_type)
        temp_handle.seek(0)

        # Save image to a SimpleUploadedFile which can be saved into
        # ImageField
        suf = SimpleUploadedFile(os.path.split(self.foto.name)[-1],
                temp_handle.read(), content_type='image/%s' % (image_type))
        # Save SimpleUploadedFile into image field
        self.thumb.save(
            'thumb_%s.%s' % (os.path.splitext(suf.name)[0], image_type),
            suf,
            save=False
        )

    def save(self, *args, **kwargs):
        self.create_thumbnail()
        force_update = False
        # If the instance already has been saved, it has an id and we set
        # force_update to True
        if self.id:
            force_update = True
        # Force an UPDATE SQL query if we're editing the image to avoid integrity exception
        super(Categoria, self).save(force_update=force_update)

    def __unicode__(self):
        return self.nome

class Evento(models.Model):
    is_active = models.BooleanField(default=True, verbose_name='Ativo?')

    categoria = models.ForeignKey(Categoria, related_name='eventos', blank=True, null=True)

    nome = models.CharField(max_length=255)
    descricao = models.TextField(verbose_name='descrição', blank=True)
    foto = models.ImageField(upload_to='img/eventos', blank=True)
    thumb = models.ImageField(upload_to='img/eventos/thumb', blank=True)
    data = models.DateField()
    local = models.TextField()
    slug = models.SlugField(max_length=150, unique=True)
    preco = models.DecimalField(max_digits=18, decimal_places=2, verbose_name='preço unitário')

    estoque = models.PositiveIntegerField()

    class Meta:
        ordering = ['nome']
        verbose_name = 'evento'
        verbose_name_plural = 'eventos'

    def decrementar_estoque(self, qtd=1):
        self.estoque -= qtd
        if self.estoque == 0:
            self.is_active = False
        self.save()

    def __unicode__(self):
        return self.nome

    @models.permalink
    def get_absolute_url(self):
        return ('detalhe_evento', (), {'evento_id': self.pk})

    # TODO: acabei fazendo o copy paste aqui, dá pra melhorar isso no futuro
    def get_thumb(self):
        return '<img src="%s%s"/>' % (MEDIA_URL, self.thumb)
    get_thumb.allow_tags = True
    get_thumb.short_description = ""

    def create_thumbnail(self):
        # original code for this method came from
        # http://snipt.net/danfreak/generate-thumbnails-in-django-with-pil/

        # If there is no image associated with this.
        # do not create thumbnail
        if not self.foto:
            return

        from PIL import Image
        from cStringIO import StringIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        import os

        # Set our max thumbnail size in a tuple (max width, max height)
        THUMBNAIL_SIZE = (50, 50)

        # Open original photo which we want to thumbnail using PIL's Image
        image = Image.open(StringIO(self.foto.read()))
        image_type = image.format.lower()

        # We use our PIL Image object to create the thumbnail, which already
        # has a thumbnail() convenience method that contrains proportions.
        # Additionally, we use Image.ANTIALIAS to make the image look better.
        # Without antialiasing the image pattern artifacts may result.
        image.thumbnail(THUMBNAIL_SIZE, Image.ANTIALIAS)

        # Save the thumbnail
        temp_handle = StringIO()
        image.save(temp_handle, image_type)
        temp_handle.seek(0)

        # Save image to a SimpleUploadedFile which can be saved into
        # ImageField
        suf = SimpleUploadedFile(os.path.split(self.foto.name)[-1],
                temp_handle.read(), content_type='image/%s' % (image_type))
        # Save SimpleUploadedFile into image field
        self.thumb.save(
            'thumb_%s.%s' % (os.path.splitext(suf.name)[0], image_type),
            suf,
            save=False
        )

    def save(self, *args, **kwargs):
        self.create_thumbnail()
        force_update = False
        # If the instance already has been saved, it has an id and we set
        # force_update to True
        if self.id:
            force_update = True
        # Force an UPDATE SQL query if we're editing the image to avoid integrity exception
        super(Evento, self).save(force_update=force_update)

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

