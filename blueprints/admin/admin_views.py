from flask import url_for, request, redirect, flash
from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView
from flask_login import current_user


class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        flash('Você não tem permissão para acessar esta página.', 'error')
        return redirect(url_for('views.home', next=request.url))

    def scaffold_list_columns(self):
        columns = super(MyModelView, self).scaffold_list_columns()
        if 'id' not in columns:
            columns.insert(0, 'id')
        return columns


class AbastecimentosView(MyModelView):
    column_filters = ['user', 'data_lanc', 'data_reg', 'motorista', 'placa', 'cidade', 'posto']
    column_searchable_list = ['id', 'user', 'data_lanc', 'data_reg', 'motorista', 'placa']
    column_default_sort = ('data_lanc', True)


class EntregaCombustivelView(MyModelView):
    column_filters = ['user', 'data_lanc', 'data_reg', 'posto']
    column_searchable_list = ['id', 'user', 'data_lanc', 'data_reg', 'posto']
    column_default_sort = ('data_lanc', True)


class PostoHistoryView(MyModelView):
    column_searchable_list = ['id_reg']


class PlacasView(MyModelView):
    column_filters = ['veiculo']
    column_searchable_list = ['placa']


class PontoViradaView(MyModelView):
    column_filters = ['posto']
    column_searchable_list = ['posto']
    column_default_sort = ('id', True)


class MotoristasView(MyModelView):
    column_filters = ['cidade']
    column_searchable_list = ['motorista']


class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        flash('Você não tem permissão para acessar esta página.', 'error')
        return redirect(url_for('views.home', next=request.url))
