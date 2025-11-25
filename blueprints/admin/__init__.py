from flask_admin import Admin
from .admin_views import *
from models import *


def init_app(app):
    admin = Admin(app, template_mode='bootstrap3', base_template='admin_template.html', url='/admin', index_view=MyAdminIndexView())
    admin.add_view(AbastecimentosView(Abastecimentos, db.session, category='Lançamentos'))
    admin.add_view(EntregaCombustivelView(EntregaCombustivel, db.session, category='Lançamentos'))
    admin.add_view(PostoHistoryView(PostoHistory, db.session, category='Lançamentos'))
    admin.add_view(PlacasView(Placas, db.session, category='Dados'))
    admin.add_view(MotoristasView(Motoristas, db.session, category='Dados'))
    admin.add_view(MyModelView(Cidades, db.session, category='Dados'))
    admin.add_view(MyModelView(Postos, db.session, category='Dados'))
    admin.add_view(PontoViradaView(PontoVirada, db.session, category='Dados'))
    admin.add_view(MyModelView(VolumeAtual, db.session, category='Dados'))
    admin.add_view(MyModelView(User, db.session, category='Dados'))
