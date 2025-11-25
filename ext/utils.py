from zoneinfo import ZoneInfo
from models import *


# cria um novo ponto de virada de preco
def create_ponto_virada(entrega: EntregaCombustivel, ab_id=None):
    ultima = (
        PontoVirada.query
        .filter_by(posto=entrega.posto)
        .order_by(PontoVirada.id.desc())
        .first()
    )
    if ultima:
        od_init = int(ultima.odometro_inicial) + int(ultima.volume)
    else:
        od_init = int(entrega.odometro)

    pv = PontoVirada(
        data=datetime.now(ZoneInfo("America/Sao_Paulo")).replace(microsecond=0),
        entrega_id=entrega.id,
        abastecimento_id=ab_id if ab_id else None,
        posto=entrega.posto,
        odometro_inicial=od_init,
        volume=entrega.volume,
        preco=entrega.preco
    )
    db.session.add(pv)
    return pv


# lida com a logica de transferencias de combustivel
def transf_fuel(collected_data, old_data=None, mode="new"):
    bomba = Postos.query.filter_by(posto=collected_data.operacao).first()
    new_data = []

    # caso de um novo registro
    if mode == "new":
        if bomba:
            # busca o odometro do ultimo abastecimento na bomba
            last_ab = Abastecimentos.query.filter_by(posto=bomba.posto).first()

            transfer_data = EntregaCombustivel(
                user=collected_data.user,
                data_lanc=collected_data.data_lanc,
                data_reg=collected_data.data_reg,
                volume=collected_data.volume,
                posto=bomba.posto,
                odometro=last_ab.odometro if last_ab else 0,
                preco=collected_data.preco
            )

            # adiciona a sessão e garante ID
            db.session.add(transfer_data)
            db.session.flush()

            # cria ponto de virada
            pv = create_ponto_virada(transfer_data, collected_data.id)

            # atualiza volume atual
            va = VolumeAtual.query.filter_by(posto=transfer_data.posto).first()
            if va:
                va.volume_restante = int(va.volume_restante) + float(transfer_data.volume)
            else:
                va = VolumeAtual(
                    posto=transfer_data.posto,
                    volume_restante=transfer_data.volume
                )
                db.session.add(va)
            return [transfer_data, pv, va]
        else:
            return None

    elif mode == "exclude":
        if not bomba:
            return None

        # ajuste de estoque
        vol = float(collected_data.volume)
        va = VolumeAtual.query.filter_by(posto=bomba.posto).first()
        if va:
            va.volume_restante = int(va.volume_restante) - vol
            new_data.append(va)

        # remove o ponto de virada desta entrega
        pv = PontoVirada.query.filter_by(abastecimento_id=collected_data.id).first()
        if pv:
            db.session.delete(pv)

        # prepara lista de entregas posteriores
        posteriores = (
            EntregaCombustivel.query
            .filter_by(posto=bomba.posto)
            .filter(
                or_(
                    EntregaCombustivel.data_reg > collected_data.data_reg,
                    and_(
                        EntregaCombustivel.data_reg == collected_data.data_reg,
                        EntregaCombustivel.id > pv.entrega_id
                    )
                )
            )
            .order_by(EntregaCombustivel.data_reg, EntregaCombustivel.id)
            .all()
        )

        # busca o ultimo ponto de virada valido antes do excluido
        pv_anterior = (
            PontoVirada.query
            .join(EntregaCombustivel, PontoVirada.entrega_id == EntregaCombustivel.id)
            .filter(EntregaCombustivel.posto == bomba.posto)
            .filter(
                or_(
                    EntregaCombustivel.data_reg < collected_data.data_reg,
                    and_(
                        EntregaCombustivel.data_reg == collected_data.data_reg,
                        EntregaCombustivel.id < pv.entrega_id
                    )
                )
            )
            .order_by(EntregaCombustivel.data_reg.desc(), EntregaCombustivel.id.desc())
            .first()
        )

        if pv_anterior:
            prev_od = pv_anterior.odometro_inicial + pv_anterior.volume
            prev_vol = pv_anterior.volume
        else:
            prev_od, prev_vol = None, None

        # recalcula todos os pontos posteriores em cadeia
        for e in posteriores:
            pv = PontoVirada.query.filter_by(entrega_id=e.id).first()
            if prev_od is not None:
                pv.odometro_inicial = prev_od
            else:
                pv.odometro_inicial = int(e.odometro)
            pv.volume = float(e.volume)
            pv.preco = e.preco
            new_data.append(pv)

            prev_od = pv.odometro_inicial + pv.volume
            prev_vol = pv.volume

        # remove a entrega de combustivel correspondente
        ent = EntregaCombustivel.query.get(pv.entrega_id)
        print(pv.entrega_id)
        db.session.delete(ent)

        return new_data

    elif mode == "edit":
        if not bomba:
            return None

        # ajusta estoque
        new_vol = float(collected_data.volume)
        old_vol = float(old_data.volume)
        new_posto = bomba.posto
        old_posto = old_data.operacao

        if old_posto == new_posto:
            va = VolumeAtual.query.filter_by(posto=new_posto).first()
            if va:
                va.volume_restante = int(va.volume_restante) - old_vol + new_vol
                new_data.append(va)
        else:
            # debita no posto antigo
            va_old = VolumeAtual.query.filter_by(posto=old_posto).first()
            if va_old:
                va_old.volume_restante = int(va_old.volume_restante) - old_vol
                new_data.append(va_old)
            # credita no posto novo
            va_new = VolumeAtual.query.filter_by(posto=new_posto).first()
            if va_new:
                va_new.volume_restante = int(va_new.volume_restante) + new_vol
            else:
                va_new = VolumeAtual(posto=new_posto, volume_restante=new_vol)
                db.session.add(va_new)
            new_data.append(va_new)

        # busca e atualiza a entrega original
        pv_current = PontoVirada.query.filter_by(abastecimento_id=old_data.id).first()
        if not pv_current:
            return None

        entrega_atual = EntregaCombustivel.query.get(pv_current.entrega_id)
        if not entrega_atual:
            return None

        entrega_atual.volume = new_vol
        entrega_atual.preco = collected_data.preco
        entrega_atual.data_lanc = collected_data.data_lanc
        entrega_atual.data_reg = collected_data.data_reg
        entrega_atual.posto = new_posto
        new_data.append(entrega_atual)

        # encontra o PontoVirada anterior ao editado
        pv_prev = (
            PontoVirada.query
            .join(EntregaCombustivel, PontoVirada.entrega_id == EntregaCombustivel.id)
            .filter(EntregaCombustivel.posto == new_posto)
            .filter(
                or_(
                    EntregaCombustivel.data_reg < entrega_atual.data_reg,
                    and_(
                        EntregaCombustivel.data_reg == entrega_atual.data_reg,
                        EntregaCombustivel.id < entrega_atual.id
                    )
                )
            )
            .order_by(EntregaCombustivel.data_reg.desc(), EntregaCombustivel.id.desc())
            .first()
        )

        if pv_prev:
            prev_od = pv_prev.odometro_inicial + pv_prev.volume
        else:
            last_ab = (
                Abastecimentos.query
                .filter_by(posto=new_posto)
                .filter(Abastecimentos.data_reg < entrega_atual.data_reg)
                .order_by(Abastecimentos.data_reg.desc(), Abastecimentos.id.desc())
                .first()
            )
            prev_od = float(last_ab.odometro) if last_ab else 0

        # atualizar o proprio PontoVirada editado
        pv_current.odometro_inicial = prev_od
        pv_current.volume = new_vol
        pv_current.preco = collected_data.preco
        new_data.append(pv_current)

        # prepara o odometro para iniciar o recalculo em cadeia
        prev_od = pv_current.odometro_inicial + pv_current.volume

        print("Oi")

        # recalcular em cadeia todos os pontos posteriores
        posteriores = (
            EntregaCombustivel.query
            .filter_by(posto=new_posto)
            .filter(
                or_(
                    EntregaCombustivel.data_reg > entrega_atual.data_reg,
                    and_(
                        EntregaCombustivel.data_reg == entrega_atual.data_reg,
                        EntregaCombustivel.id > entrega_atual.id
                    )
                )
            )
            .order_by(EntregaCombustivel.data_reg, EntregaCombustivel.id)
            .all()
        )

        for ent in posteriores:
            pv_next = PontoVirada.query.filter_by(entrega_id=ent.id).first()
            if not pv_next:
                continue

            pv_next.odometro_inicial = prev_od
            new_data.append(pv_next)

            prev_od = pv_next.odometro_inicial + pv_next.volume

        return new_data
