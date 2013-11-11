# -*- coding: UTF-8 -*-

import reportengine
from reportengine.filtercontrols import StartsWithFilterControl
from tt.models import *

class UsuarioReport(reportengine.ModelReport):
    """ Relatório de usuário """
    verbose_name = "Relatório de Usuários"
    slug = "relatorio-usuarios"
    namespace = "usuario"
    description = "Lista todos os usuários presentes no sistema"
    labels = ('username','is_active','email','nome')
    list_filter=['is_active','data_nascimento', StartsWithFilterControl('username'), StartsWithFilterControl('email')]
    date_field = "data_nascimento" # Allows auto filtering by this date
    model=Usuario
    per_page = 500

reportengine.register(UsuarioReport)