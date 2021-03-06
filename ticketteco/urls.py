# -*- coding: UTF-8 -*-
from django.conf import settings

from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from tt.views import  *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
import reportengine

reportengine.autodiscover()
admin.autodiscover()

urlpatterns = patterns('',

    url(r'^$', Index.as_view(), name='index'),

    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'tt/login.html'}, name='login'),

    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '../'}, name='logout'),

    url(r'^carrinho/$', mostrar_carrinho, name='carrinho'),

    url(r'^catalogo/$', Catalogo.as_view(), name='catalogo'),

    url(r'^catalogo/(?P<evento_id>\d+)/$', mostrar_detalhe_evento, name='detalhe_evento'),

    url(r'^busca/$', mostrar_busca, name='busca'),

    url(r'^categoria/(?P<slug>[\w-]+)/$', CategoriaListView.as_view(), name = 'detalhe_categoria'),

    url(r'^pedidos/$', mostrar_lista_pedidos, name='meus_pedidos'),

    url(r'^pedidos/(?P<pedido_id>\d+)/$', mostrar_detalhe_pedido, name='detalhe_pedido'),

    url(r'^cadastro/$', mostrar_cadastro, name='cadastro'),

    url(r'^alteracao/$', mostrar_alteracao, name='alteracao'),

    url(r'^selecao_endereco/$', mostrar_selecao_endereco, name='selecao_endereco'),

    url(r'^checkout/$', mostrar_checkout, name='checkout'),

    url(r'^relatorios/', include('reportengine.urls')),
    url(r'^admin/', include(admin.site.urls)),

)

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
