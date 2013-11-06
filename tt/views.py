# -*- coding: UTF-8 -*-
from decimal import Decimal
import threading

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic.list import ListView

from tt.forms import EventoDetalheForm, UsuarioCadastroForm, EnderecoCadastroForm

from tt.models import Evento, Endereco, Pedido, Item


class Index(ListView):
    model = Evento
    queryset = Evento.objects.filter(is_active=True).order_by('-data')[:3]
    template_name = 'tt/index.html'

class Catalogo(ListView):
    model = Evento
    queryset = Evento.objects.filter(is_active=True).order_by('-data')
    template_name = 'tt/catalogo.html'

def mostrar_detalhe_evento(request, evento_id):
    evento = get_object_or_404(Evento.objects.filter(is_active=True, pk=evento_id))

    if request.method == 'POST':
        form = EventoDetalheForm(request.POST)

        if form.is_valid():
            try:
                carrinho = Carrinho(request.session)
                carrinho.add(evento=evento, preco=evento.preco, quantidade=form.cleaned_data.get('quantidade'))
                messages.success(request, 'O carrinho foi atualizado.')

            except ValidationError, e:
                if e.code == 'order_sealed':
                    [messages.error(request, msg) for msg in e.messages]

            return redirect('carrinho')
    else:
        form = EventoDetalheForm()

    return render(request, 'tt/detalhe_evento.html', {
        'object': evento,
        'form': form,
        },)

@login_required()
def mostrar_detalhe_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido.objects.filter(pk=pedido_id, user=request.user))
    return render(request, 'tt/detalhe_pedido.html', {'pedido':pedido})

@login_required()
def mostrar_lista_pedidos(request):
    pedidos = Pedido.objects.filter(user=request.user)
    return render(request, 'tt/lista_pedidos.html', {'pedidos':pedidos})

def mostrar_cadastro(request):
    if request.method == 'POST':
        form = UsuarioCadastroForm(request.POST)
        form_end = EnderecoCadastroForm(request.POST)
        if form.is_valid() and form_end.is_valid():
            try:
                novo_usuario = form.save()
                novo_endereco = form_end.save(commit=False)
                novo_usuario.enderecos.add(novo_endereco)
                novo_usuario.save()
                messages.success(request, 'Usuário cadastrado.')
                novo_usuario = authenticate(username=request.POST['username'],
                                    password=request.POST['password1'])
                login(request, novo_usuario)
                if 'next' in request.session and request.session['next']:
                    proximo = request.session['next']
                    del request.session['next']
                    request.session.modified = True
                    return redirect(proximo)
                else:
                    return redirect('catalogo')
            except ValidationError, e:
                if e:
                    [messages.error(request, msg) for msg in e.messages]

    else:
        form = UsuarioCadastroForm()
        form_end = EnderecoCadastroForm()
        if 'next' in request.GET and request.GET['next']:
            proximo = request.GET['next']
            request.session['next'] = proximo
    return render(request, "tt/cadastro_usuario.html", {'form':form, 'form_end':form_end,})

@login_required
def mostrar_checkout(request):
    # método aninhado para fazer a conversão dos itens do carrinho para objetos de item
    def carrinho_para_pedido(pedido):
        cart_items = Carrinho(request.session).items
        for item in cart_items:
            i = Item(evento=item.evento, quantidade=item.quantidade)
            pedido.items.add(i)

    def disponibilidade_estoque():
        # TODO: poderia melhorar isso, talvez usando signals
        cart_items = Carrinho(request.session).items
        eventos_para_atualizar = []
        for item in cart_items:
            if item.quantidade > item.evento.estoque:
                return (False, "Evento Esgotado")
            elif item.quantidade <= item.evento.estoque:
                eventos_para_atualizar.append((item.evento, item.quantidade))
        for evento, qtd in eventos_para_atualizar:
            evento.decrementar_estoque(qtd)
        return (True, None)

    def envia_email(recipiente, mensagem):
        send_mail('Ticket Teco - Confirmação de Pedido', mensagem, 'raulvc@gmail.com',
                          [recipiente], fail_silently=True)

    if not Carrinho(request.session).items:
        return redirect('carrinho')
    elif 'endereco_entrega_id' not in request.session or not request.session['endereco_entrega_id']:
        return redirect('selecao_endereco')

    else:
        endereco = Endereco.objects.filter(id=request.session['endereco_entrega_id'])[0]
        if request.method == 'POST':
            # pedido foi confirmado
            try:
                (ok, msg) = disponibilidade_estoque()
                if not ok:
                    return render(request, 'tt/erro.html', {'mensagem':msg})

                pedido = Pedido.objects.create(user=request.user, endereco_entrega=endereco, status=10,
                                metodo_envio='correio', total=0)
                carrinho_para_pedido(pedido)
                pedido.recalcula_total(save=True)

                Carrinho(request.session).clear()

                mensagem = """\
                Seu pedido de número %s foi confirmado.
                Obrigado por comprar conosco!
                Você pode acessar seu pedido em http://127.0.0.1:8000/pedidos/%s\
                """ % (pedido.id, pedido.id)

                # tornando o envio de email uma thread para não bloquear o cliente
                t = threading.Thread(target=envia_email, args=[request.user.email, mensagem],)
                t.setDaemon(True)
                t.start()

                return render(request, 'tt/pedido_confirmado.html', {'p_id':pedido.id})

            except Exception, e:
                print e.message
                messages.error(request, 'Problema na confirmação do pedido')

        return render(request, 'tt/checkout.html', {'end':endereco,})

@login_required
def mostrar_selecao_endereco(request):
    enderecos = Endereco.objects.filter(user=request.user)
    if request.method == 'POST':
        request.session['endereco_entrega_id'] = request.POST['endereco']
        return redirect('checkout')
    return render(request, 'tt/selecao_endereco.html', {'enderecos':enderecos,})

def mostrar_carrinho(request):
    return render(request, 'tt/carrinho.html')

# reside na sessão, sem muita certeza de em que arquivo colocar
class Carrinho(object):
    def __init__(self, session):
        self._items_dict = {}
        self.session = session
        session_key = 'carrinho'
        if session_key in self.session:
            self._items_dict = session[session_key]._items_dict
        self.session[session_key] = self

    def __contains__(self, evento):
        """
        Checks if the given product is in the cart.
        """
        return evento in self.eventos

    def add(self, evento, setor=None, quantidade=1, preco=None):
        """
        Adds or creates products in cart. For an existing product,
        the quantity is increased and the price is ignored.
        """
        quantidade = int(quantidade)
        if quantidade < 1:
            raise ValueError('Quantity must be at least 1 when adding to cart')
        if evento in self.eventos:
            self._items_dict[evento.pk].quantidade += quantidade
        else:
            if preco == None:
                raise ValueError('Missing price when adding to cart')
            self._items_dict[evento.pk] = CarrinhoItem(evento, setor, quantidade, preco)
        self.session.modified = True

    def remove(self, evento):
        if evento in self.eventos:
            del self._items_dict[evento.pk]
            self.session.modified = True

    def clear(self):
        """
        Removes all items.
        """
        self._items_dict = {}
        self.session.modified = True

    def set_quantity(self, evento, quantidade):
        if evento not in self.eventos:
            return
        quantidade = int(quantidade)
        if quantidade < 0:
            raise ValueError('Quantity must be positive when updating cart')
        self._items_dict[evento.pk].quantidade = quantidade
        if self._items_dict[evento.pk].quantidade < 1:
            del self._items_dict[evento.pk]
        self.session.modified = True

    def is_empty(self):
        return len(self._items_dict) <= 0

    @property
    def items(self):
        """
        The list of cart items.
        """
        return self._items_dict.values()

    @property
    def eventos(self):
        """
        The list of associated products.
        """
        return [item.evento for item in self.items]

    @property
    def total(self):
        """
        The total value of all items in the cart.
        """
        return sum([item.subtotal for item in self.items])

class CarrinhoItem(object):
    def __init__(self, evento, setor=None, quantidade=1, preco=None):
        self.evento = evento
        self.setor = setor
        self.quantidade = int(quantidade)
        self.preco = Decimal(str(preco))

    def __repr__(self):
        return u'Objeto de CarrinhoItem (%s)' % self.evento

    @property
    def subtotal(self):
        return self.preco * self.quantidade