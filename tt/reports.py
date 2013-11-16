# -*- coding: UTF-8 -*-
from django.db.models import Sum, Count

import reportengine
from reportengine.filtercontrols import StartsWithFilterControl, DateTimeFilterControl
from tt.models import *

class UsuarioReport(reportengine.ModelReport):
    """ Relatório de usuários """
    verbose_name = "Todos os Usuários"
    slug = "relatorio-usuarios"
    namespace = "usuario"
    description = "Lista todos os usuários presentes no sistema"

    labels = ('username','is_active','email','nome', 'data_nascimento')
    list_filter = ['is_active', DateTimeFilterControl('data_nascimento'),
                 StartsWithFilterControl('username'), StartsWithFilterControl('email')]
    date_field = 'data_nascimento' # Allows auto filtering by this date
    model = Usuario
    per_page = 100

class EventoReport(reportengine.ModelReport):
    """ Relatório de eventos """
    verbose_name = "Todos os Eventos"
    slug = "relatorio-eventos"
    namespace = "evento"
    description = "Lista todos os eventos presentes no sistema"

    labels = ('is_active', 'nome', 'descricao', 'data', 'local', 'preco', 'estoque_inicial', 'estoque')
    list_filter = ['is_active', DateTimeFilterControl('data'),
                 StartsWithFilterControl('nome'), StartsWithFilterControl('descricao')]
    date_field = 'data' # Allows auto filtering by this date
    model = Evento
    per_page = 100

class CategoriaReport(reportengine.ModelReport):
    """ Relatório de categorias """
    verbose_name = "Todos as Categorias"
    slug = "relatorio-categorias"
    namespace = "categoria"
    description = "Lista todas as categorias presentes no sistema"

    labels = ('is_active', 'nome', 'descricao')
    list_filter = ['is_active', StartsWithFilterControl('nome'), StartsWithFilterControl('descricao')]
    model = Categoria
    per_page = 100

class PedidoReport(reportengine.ModelReport):
    """ Relatório de pedidos """
    verbose_name = "Todos os Pedidos"
    slug = "relatorio-pedidos"
    namespace = "pedido"
    description = "Listagem de pedidos"

    labels = ('data_criado', 'user', 'status', 'endereco_entrega', 'metodo_envio', 'total')
    list_filter = [DateTimeFilterControl('data_criado'),
                   StartsWithFilterControl('user')]
    date_field = 'data_criado'
    model = Pedido
    per_page = 100

class PedidoConfirmadoReport(reportengine.QuerySetReport):
    """ Pedidos Confirmados """

    queryset = Pedido.objects.filter(status=10)

    verbose_name = "Pedidos Confirmados"
    slug = "relatorio-pedidos-confirmados"
    namespace = "pedido"
    description = "Listagem de pedidos confirmados"
    labels = ('data_criado', 'user', 'endereco_entrega', 'metodo_envio', 'total')
    list_filter = [DateTimeFilterControl('data_criado'),
                   StartsWithFilterControl('user')]
    date_field = 'data_criado'
    per_page = 100

class PedidoMaioresCompradoresReport(reportengine.QuerySetReport):
    queryset = Pedido.objects.values('user').annotate(total_comprado=Sum('total')).order_by('-total_comprado')

    verbose_name = "Maiores Compradores"
    slug = "relatorio-pedidos-maiores-compradores"
    namespace = "pedido"
    description = "Maiores Compradores"

    labels = ('user', 'total_comprado')
    per_page = 100

class PedidoFrequentesCompradoresReport(reportengine.QuerySetReport):
    queryset = Pedido.objects.values('user').annotate(frequencia=Count('user')).order_by('-frequencia')

    verbose_name = "Frequentes Compradores"
    slug = "relatorio-pedidos-frequentes-compradores"
    namespace = "pedido"
    description = "Frequentes Compradores"

    labels = ('user', 'frequencia')
    per_page = 100

class PedidoVendasPorDiaReport(reportengine.QuerySetReport):
    queryset = Pedido.objects.extra({'data' : "date(data_criado)"}).values('data').annotate(total_comprado=Sum('total')).order_by('-data')

    verbose_name = "Total de Vendas por Dia"
    slug = "relatorio-pedidos-vendas-por-dia"
    namespace = "pedido"
    description = "Lista o total de vendas por dia"

    labels = ('data', 'total_comprado')
    per_page = 100

class PedidoVendasPorMesReport(reportengine.QuerySetReport):
    queryset = Pedido.objects.extra({'data' : "MONTH(data_criado)"}).values('data').annotate(total_comprado=Sum('total')).order_by('-data')

    verbose_name = "Total de Vendas por Mês"
    slug = "relatorio-pedidos-vendas-por-mes"
    namespace = "pedido"
    description = "Lista o total de vendas por mês"

    labels = ('data', 'total_comprado')
    per_page = 100

reportengine.register(UsuarioReport)
reportengine.register(CategoriaReport)
reportengine.register(EventoReport)
reportengine.register(PedidoReport)
reportengine.register(PedidoConfirmadoReport)
reportengine.register(PedidoMaioresCompradoresReport)
reportengine.register(PedidoFrequentesCompradoresReport)
reportengine.register(PedidoVendasPorDiaReport)
reportengine.register(PedidoVendasPorMesReport)