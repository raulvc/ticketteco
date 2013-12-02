# -*- coding: UTF-8 -*-
from decimal import Decimal
from itertools import chain
from operator import attrgetter
import threading

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic.list import ListView

from tt.forms import EventoDetalheForm, UsuarioCadastroForm, UsuarioAlteracaoForm, EnderecoCadastroFormSet

from tt.models import Evento, Endereco, Pedido, Item, Categoria

# TODO: endereço

# class-based views do django 1.5, não são fáceis de entender como o método tradicional mas ocupam menos linhas
class Index(ListView):
    model = Evento
    queryset = Evento.objects.filter(is_active=True).order_by('-data')[:3]
    template_name = 'tt/index.html'

class Catalogo(ListView):
    model = Evento
    template_name = 'tt/catalogo.html'

    def get_context_data(self, **kwargs):
        context = super(Catalogo, self).get_context_data(**kwargs)
        # 5 próximos
        context['proximos'] = Evento.objects.filter(is_active=True).order_by('data')[:5]
        # mais populares
        context['ultimos'] = Evento.objects.filter(is_active=True).order_by('estoque')[:5]
        # só o topo da hierarquia
        context['categorias'] = Categoria.objects.all().exclude(pai__isnull=False)
        return context

class CategoriaListView(ListView):
    model = Categoria
    template_name = 'tt/detalhe_categoria.html'

    def get_context_data(self, **kwargs):
        context = super(CategoriaListView, self).get_context_data(**kwargs)
        if 'slug' in self.kwargs:
            context['object'] = get_object_or_404(Categoria.objects.filter(slug=self.kwargs['slug']))
            context['eventos'] = Evento.objects.filter(is_active=True, categoria=context['object']).order_by('data', 'nome')
        return context

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

            except ValueError:
                messages.error(request, "Número máximo de tickets atingido")

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
    pedidos = Pedido.objects.filter(user=request.user).order_by('-id')
    return render(request, 'tt/lista_pedidos.html', {'pedidos':pedidos})

def mostrar_cadastro(request):
    if request.method == 'POST':
        form = UsuarioCadastroForm(request.POST)
        formset_end = EnderecoCadastroFormSet(request.POST)
        if form.is_valid() and formset_end.is_valid():
            try:
                novo_usuario = form.save()
                for form_end in formset_end.forms:
                    end = form_end.save(commit=False)
                    novo_usuario.enderecos.add(end)
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
        formset_end = EnderecoCadastroFormSet()
        if 'next' in request.GET and request.GET['next']:
            proximo = request.GET['next']
            request.session['next'] = proximo
    return render(request, "tt/cadastro_usuario.html", {'form':form, 'formset_end':formset_end,})

@login_required
def mostrar_alteracao(request):
    if request.method == 'POST':

        form = UsuarioAlteracaoForm(request.POST, instance=request.user)

        if form.is_valid():
            try:
                usr = form.save()
                messages.success(request, 'Dados alterados.')
                return render(request, 'tt/sucesso.html', {'mensagem':'Alteração Concluída'})

            except ValidationError, e:
                if e:
                    [messages.error(request, msg) for msg in e.messages]
    else:
        form = UsuarioAlteracaoForm(instance=request.user)

    return render(request, "tt/alteracao_usuario.html", {'form':form,})

@login_required
def mostrar_checkout(request):
    # método aninhado para fazer a conversão dos itens do carrinho para objetos de item
    def carrinho_para_pedido(pedido):
        cart_items = Carrinho(request.session).items
        for item in cart_items:
            i = Item(evento=item.evento, quantidade=item.quantidade)
            pedido.items.add(i)

    def disponibilidade_estoque():
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

def mostrar_busca(request):
    chave = request.GET.get('chave', '')
    categorias = Categoria.objects.filter(nome__icontains=chave)
    eventos = Evento.objects.filter(nome__icontains=chave)
    objetos = sorted(chain(categorias, eventos), key=attrgetter('nome'))
    return render(request, 'tt/busca.html',{'objetos':objetos, 'chave':chave,})

def mostrar_carrinho(request):
    if request.method == 'POST':
        carrinho = Carrinho(request.session)
        if 'clear' in request.POST:
            carrinho.clear()
        else:
            evento = get_object_or_404(Evento.objects.filter(id=request.POST['evento_id']))
            qtd = int(request.POST['qtd'])
            try:
                if 'inc' in request.POST:
                    carrinho.set_quantity(evento, qtd+1)
                else:
                    carrinho.set_quantity(evento, qtd-1)
            except ValueError:
                messages.error(request, "Número máximo de tickets atingido")

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

    def add(self, evento, quantidade=1, preco=None):
        """
        Adds or creates products in cart. For an existing product,
        the quantity is increased and the price is ignored.
        """
        quantidade = int(quantidade)
        if quantidade < 1:
            raise ValueError('Quantity must be at least 1 when adding to cart')
        if evento in self.eventos:
            # já existe no carrinho, apenas atualizar quantidade
            qtd = self.get_quantity(evento)
            self.set_quantity(evento, qtd + quantidade)
        else:
            if preco == None:
                raise ValueError('Missing price when adding to cart')
            self._items_dict[evento.pk] = CarrinhoItem(evento, quantidade, preco)
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

    def get_quantity(self, evento):
        if evento in self.eventos:
            return self._items_dict[evento.pk].quantidade
        else:
            return None

    def set_quantity(self, evento, quantidade):
        if evento not in self.eventos:
            return
        elif quantidade < 0 or quantidade > 5:
            raise ValueError
        else:
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
    def __init__(self, evento, quantidade=1, preco=None):
        self.evento = evento
        self.quantidade = int(quantidade)
        self.preco = Decimal(str(preco))

    def __repr__(self):
        return u'Objeto de CarrinhoItem (%s)' % self.evento

    @property
    def subtotal(self):
        return self.preco * self.quantidade