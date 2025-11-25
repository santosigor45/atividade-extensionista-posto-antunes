from flask import request, jsonify
from flask_login import current_user
from models import *
from types import SimpleNamespace
from ext.utils import create_ponto_virada, transf_fuel
from datetime import datetime
from zoneinfo import ZoneInfo


def send_data(data_to_send, collected_data, message):
    try:
        if collected_data:
            data_to_send.append(collected_data)

        if data_to_send:
            for data in data_to_send:
                db.session.merge(data)

        db.session.commit()
        return jsonify({'type': 'success', 'message': message})

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'type': 'error',
            'message': 'Ocorreu um erro, por favor contate o administrador.',
            'error': 'db error:' + str(e)
        })


def edit_form(form_id):
    try:
        data_to_send = []
        message = 'Dados alterados com sucesso!'

        # editar placas
        if form_id == "editFormPlacas":
            collected_data = Placas.query.get(request.form.get('id'))
            duplicado = Placas.query.filter_by(placa=request.form.get('placa')).all()

            # inserir nova placa
            if not collected_data:
                if not duplicado:
                    collected_data = Placas(
                        placa=request.form.get('placa'),
                        veiculo=request.form.get('veiculo'),
                        modelo=request.form.get('modelo'),
                        qrcode=request.form.get('qrcode'),
                        km_ideal=str(f"{round(float(request.form.get('km_ideal')), 2) or 0.00:.2f}"),
                        ativo=bool(request.form.get('ativo'))
                    )
                    data_to_send.append(collected_data)
                    message = 'Placa cadastrada com sucesso!'
                    return send_data(data_to_send, collected_data, message)
                else:
                    return jsonify({'type': 'info', 'message': 'Placa já cadastrada!'})

            # atualizar placa existente
            if (len(duplicado) == 1 and duplicado[0].id == collected_data.id) or not duplicado:
                fields = [
                    ('placa', 'placa'),
                    ('veiculo', 'veiculo'),
                    ('modelo', 'modelo'),
                    ('qrcode', 'qrcode'),
                    ('km_ideal', lambda: str(f"{round(float(request.form.get('km_ideal')), 2) or 0.00:.2f}")),
                    ('ativo', lambda: bool(request.form.get('ativo')))
                ]
            else:
                return jsonify({'type': 'info', 'message': 'Placa já cadastrada!'})

            # aplica alteracoes e registra historico
            col_alteradas = "placas: "
            val_antigo = ""
            for attr, form_field in fields:
                old = getattr(collected_data, attr)
                new = form_field() if callable(form_field) else request.form.get(form_field)
                if str(old) != str(new):
                    val_antigo += f"({old}), "
                    col_alteradas += f"({attr}), "
                    setattr(collected_data, attr, new)

            if not val_antigo:
                return jsonify({'type': 'info', 'message': 'Nenhum dado alterado!'})

            # trim virgulas finais
            col_alteradas = col_alteradas[:-2]
            val_antigo = val_antigo[:-2]

            history = PostoHistory(
                id_reg=collected_data.id,
                data_edicao=datetime.now(ZoneInfo("America/Sao_Paulo")).replace(microsecond=0),
                user=current_user.username,
                colunas_alteradas=col_alteradas,
                valores_antigos=val_antigo
            )

            data_to_send.append(history)
            data_to_send.append(collected_data)
            return send_data(data_to_send, collected_data, message)

        # editar motoristas
        elif form_id == "editFormMotoristas":
            collected_data = Motoristas.query.get(request.form.get('id'))
            duplicado = Motoristas.query.filter_by(motorista=request.form.get('motorista')).all()

            # inserir novo motorista
            if not collected_data:
                if not duplicado:
                    collected_data = Motoristas(
                        motorista=request.form.get('motorista'),
                        cidade=request.form.get('cidade')
                    )
                    data_to_send.append(collected_data)
                    message = 'Motorista cadastrado com sucesso!'
                    return send_data(data_to_send, collected_data, message)
                else:
                    return jsonify({'type': 'info', 'message': 'Motorista já cadastrado!'})

            # atualizar motorista existente
            if (len(duplicado) == 1 and duplicado[0].id == collected_data.id) or not duplicado:
                fields = [
                    ('motorista', 'motorista'),
                    ('cidade', 'cidade')
                ]
            else:
                return jsonify({'type': 'info', 'message': 'Motorista já cadastrado!'})

            # aplica alteracoes e registra historico
            col_alteradas = "motoristas: "
            val_antigo = ""
            for attr, form_field in fields:
                old = getattr(collected_data, attr)
                new = form_field() if callable(form_field) else request.form.get(form_field)
                if str(old) != str(new):
                    val_antigo += f"({old}), "
                    col_alteradas += f"({attr}), "
                    setattr(collected_data, attr, new)

            if not val_antigo:
                return jsonify({'type': 'info', 'message': 'Nenhum dado alterado!'})

            col_alteradas = col_alteradas[:-2]
            val_antigo = val_antigo[:-2]
            history = PostoHistory(
                id_reg=collected_data.id,
                data_edicao=datetime.now(ZoneInfo("America/Sao_Paulo")).replace(microsecond=0),
                user=current_user.username,
                colunas_alteradas=col_alteradas,
                valores_antigos=val_antigo
            )
            data_to_send.append(history)
            data_to_send.append(collected_data)
            return send_data(data_to_send, collected_data, message)

        # editar abastecimentos
        elif form_id == "editFormAbastecimentos":
            ab = Abastecimentos.query.get(request.form.get("id"))
            if not ab:
                return jsonify({'type': 'error', 'message': 'Abastecimento não encontrado!'})

            # persiste valores uteis antes da atualizacao
            old_data = SimpleNamespace(**ab.to_dict())
            old_vol = float(ab.volume)
            old_posto = ab.posto
            old_operacao = ab.operacao

            fields = [
                ('data_reg', 'data'),
                ('motorista', 'motorista'),
                ('placa', 'placa'),
                ('operacao', 'operacao'),
                ('observacoes', 'observacoes'),
                ('quilometragem', 'quilometragem'),
                ('volume', 'volume'),
                ('cidade', 'cidade'),
                ('posto', 'posto'),
                ('odometro', 'odometro'),
                ('combustivel', 'combustivel'),
                ('preco', lambda: request.form.get('preco', '').replace(',', '.'))
            ]

            # aplica alteracoes e registra historico
            col_alteradas = "abastecimentos: "
            val_antigo = ""
            for attr, form_field in fields:
                old = ab.data_reg.strftime('%Y-%m-%d') if attr == 'data_reg' else getattr(ab, attr)
                new = form_field() if callable(form_field) else request.form.get(form_field) or None
                if attr in ('quilometragem', 'volume', 'odometro') and new is not None:
                    new = str(new)
                if str(old) != str(new):
                    val_antigo += f"({old}), "
                    col_alteradas += f"({attr}), "
                    setattr(ab, attr, new)

            if not val_antigo:
                return jsonify({'type': 'info', 'message': 'Nenhum dado alterado!'})

            col_alteradas = col_alteradas[:-2]
            val_antigo = val_antigo[:-2]
            history = PostoHistory(
                id_reg=ab.id,
                data_edicao=datetime.now(ZoneInfo("America/Sao_Paulo")).replace(microsecond=0),
                user=current_user.username,
                colunas_alteradas=col_alteradas,
                valores_antigos=val_antigo
            )
            data_to_send.append(history)

            # ajusta o estoque
            new_vol = float(ab.volume)
            new_posto = ab.posto
            if old_posto == new_posto:
                va = VolumeAtual.query.filter_by(posto=new_posto).first()
                if va:
                    va.volume_restante = int(va.volume_restante) + old_vol - new_vol
                    data_to_send.append(va)
            else:
                va_old = VolumeAtual.query.filter_by(posto=old_posto).first()
                if va_old:
                    va_old.volume_restante = int(va_old.volume_restante) + old_vol
                    data_to_send.append(va_old)
                va_new = VolumeAtual.query.filter_by(posto=new_posto).first()
                if va_new:
                    va_new.volume_restante = int(va_new.volume_restante) - new_vol
                    data_to_send.append(va_new)

            # lida com a logica de transferencia de combustivel
            new_operacao = ab.operacao
            if old_operacao or new_operacao:
                if old_operacao:
                    if new_operacao is None:
                        data_to_send.extend(transf_fuel(collected_data=old_data, mode="exclude"))
                    else:
                        data_to_send.extend(transf_fuel(ab, old_data, "edit"))
                elif old_operacao is None and new_operacao:
                    data_to_send.extend(transf_fuel(ab, mode="new"))

            message = 'Abastecimento alterado com sucesso!'
            return send_data(data_to_send, ab, message)

        # editar entrega de combustivel
        elif form_id == "editFormEntregaCombustivel":
            ent = EntregaCombustivel.query.get(request.form.get("id"))
            if not ent:
                return jsonify({'type': 'error', 'message': 'Entrega não encontrada!'})

            old_vol = float(ent.volume)
            old_posto = ent.posto
            old_data_reg = ent.data_reg
            old_od = int(ent.odometro)

            fields = [
                ('data_reg', 'data'),
                ('volume', 'volume'),
                ('posto', 'posto'),
                ('odometro', 'odometro'),
                ('preco', lambda: request.form.get('preco', '').replace(',', '.'))
            ]

            # aplica alteracoes e registra historico
            col_alteradas = "entrega_combustivel: "
            val_antigo = ""
            for attr, form_field in fields:
                old = ent.data_reg.strftime('%Y-%m-%d') if attr == 'data_reg' else getattr(ent, attr)
                new = form_field() if callable(form_field) else request.form.get(form_field) or None
                if attr in ('volume', 'odometro') and new is not None:
                    new = str(new)
                if str(old) != str(new):
                    val_antigo += f"({old}), "
                    col_alteradas += f"({attr}), "
                    setattr(ent, attr, new)

            if not val_antigo:
                return jsonify({'type': 'info', 'message': 'Nenhum dado alterado!'})

            col_alteradas = col_alteradas[:-2]
            val_antigo = val_antigo[:-2]
            history = PostoHistory(
                id_reg=ent.id,
                data_edicao=datetime.now(ZoneInfo("America/Sao_Paulo")).replace(microsecond=0),
                user=current_user.username,
                colunas_alteradas=col_alteradas,
                valores_antigos=val_antigo
            )
            data_to_send.append(history)

            # ajustar estoque
            new_vol = float(ent.volume)
            new_posto = ent.posto
            if old_posto == new_posto:
                va = VolumeAtual.query.filter_by(posto=new_posto).first()
                if va:
                    va.volume_restante = int(va.volume_restante) - old_vol + new_vol
                    data_to_send.append(va)
            else:
                va_old = VolumeAtual.query.filter_by(posto=old_posto).first()
                if va_old:
                    va_old.volume_restante = int(va_old.volume_restante) - old_vol
                    data_to_send.append(va_old)
                va_new = VolumeAtual.query.filter_by(posto=new_posto).first()
                if va_new:
                    va_new.volume_restante = int(va_new.volume_restante) + new_vol
                    data_to_send.append(va_new)

            # recalcular pontos de virada
            posteriores = (
                EntregaCombustivel.query
                .filter_by(posto=ent.posto)
                .filter(
                    or_(
                        EntregaCombustivel.data_reg > old_data_reg,
                        and_(
                            EntregaCombustivel.data_reg == old_data_reg,
                            EntregaCombustivel.id > ent.id
                        )
                    )
                )
                .order_by(EntregaCombustivel.data_reg, EntregaCombustivel.id)
                .all()
            )

            pv_anterior = (
                PontoVirada.query
                .join(EntregaCombustivel, PontoVirada.entrega_id == EntregaCombustivel.id)
                .filter(EntregaCombustivel.posto == ent.posto)
                .filter(
                    or_(
                        EntregaCombustivel.data_reg < old_data_reg,
                        and_(
                            EntregaCombustivel.data_reg == old_data_reg,
                            EntregaCombustivel.id < ent.id
                        )
                    )
                )
                .order_by(EntregaCombustivel.data_reg.desc(), EntregaCombustivel.id.desc())
                .first()
            )

            if pv_anterior:
                prev_od = pv_anterior.odometro_inicial + pv_anterior.volume
            else:
                prev_od = None

            # atualiza ponto atual
            pv = PontoVirada.query.filter_by(entrega_id=ent.id).first()
            if pv:
                pv.odometro_inicial = prev_od if prev_od is not None else int(ent.odometro)
                pv.volume = float(ent.volume)
                pv.preco = ent.preco
                data_to_send.append(pv)
                prev_od = pv.odometro_inicial + pv.volume

            # atualiza pontos posteriores
            for e in posteriores:
                pv = PontoVirada.query.filter_by(entrega_id=e.id).first()
                if pv:
                    pv.odometro_inicial = prev_od if prev_od is not None else int(e.odometro)
                    pv.volume = float(e.volume)
                    pv.preco = e.preco
                    data_to_send.append(pv)
                    prev_od = pv.odometro_inicial + pv.volume

            message = 'Entrega de combustível alterada com sucesso!'
            return send_data(data_to_send, ent, message)

        # Formulário não reconhecido
        return jsonify({'type': 'error', 'message': 'Formulário não suportado!'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'type': 'error', 'message': 'function error: ' + str(e)})


def delete_form(form_id):
    try:
        data_to_send = []
        collected_data = None
        message = 'Dados excluídos com sucesso!'

        if form_id.startswith("deleteForm"):
            table_id = form_id.replace("deleteForm", "").lower()

            # excluir entrega de combustível
            if table_id == "entrega_combustivel":
                ent = EntregaCombustivel.query.get(request.form.get("id"))
                if not ent:
                    return jsonify({'type': 'error', 'message': 'Entrega não encontrada!'})

                # historico de exclusao
                col_alteradas = ", ".join(f"({col.name})" for col in ent.__table__.columns)
                val_antigo = ", ".join(f"({getattr(ent, col.name)})" for col in ent.__table__.columns)
                history = PostoHistory(
                    id_reg=ent.id,
                    data_edicao=datetime.now(ZoneInfo("America/Sao_Paulo")).replace(microsecond=0),
                    user=current_user.username,
                    colunas_alteradas=col_alteradas,
                    valores_antigos=val_antigo
                )
                data_to_send.append(history)

                # ajuste de estoque
                vol = float(ent.volume)
                va = VolumeAtual.query.filter_by(posto=ent.posto).first()
                if va:
                    va.volume_restante = int(va.volume_restante) - vol
                    data_to_send.append(va)

                # remove o ponto de virada desta entrega
                pv_del = PontoVirada.query.filter_by(entrega_id=ent.id).first()
                if pv_del:
                    db.session.delete(pv_del)

                # prepara lista de entregas posteriores
                posteriores = (
                    EntregaCombustivel.query
                    .filter_by(posto=ent.posto)
                    .filter(
                        or_(
                            EntregaCombustivel.data_reg > ent.data_reg,
                            and_(
                                EntregaCombustivel.data_reg == ent.data_reg,
                                EntregaCombustivel.id > ent.id
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
                    .filter(EntregaCombustivel.posto == ent.posto)
                    .filter(
                        or_(
                            EntregaCombustivel.data_reg < ent.data_reg,
                            and_(
                                EntregaCombustivel.data_reg == ent.data_reg,
                                EntregaCombustivel.id < ent.id
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
                    data_to_send.append(pv)

                    prev_od = pv.odometro_inicial + pv.volume
                    prev_vol = pv.volume

                # deleta a entrega
                db.session.delete(ent)
                message = 'Entrega de combustível excluída com sucesso!'

            # excluir abastecimento
            elif table_id == "abastecimentos":
                ab = Abastecimentos.query.get(request.form.get("id"))
                if not ab:
                    return jsonify({'type': 'error', 'message': 'Abastecimento não encontrado!'})

                # historico
                col_alteradas = ", ".join(f"({col.name})" for col in ab.__table__.columns)
                val_antigo = ", ".join(f"({getattr(ab, col.name)})" for col in ab.__table__.columns)
                history = PostoHistory(
                    id_reg=ab.id,
                    data_edicao=datetime.now(ZoneInfo("America/Sao_Paulo")).replace(microsecond=0),
                    user=current_user.username,
                    colunas_alteradas=col_alteradas,
                    valores_antigos=val_antigo
                )
                data_to_send.append(history)

                # ajuste de estoque
                vol = float(ab.volume)
                va = VolumeAtual.query.filter_by(posto=ab.posto).first()
                if va:
                    va.volume_restante = int(va.volume_restante) + vol
                    data_to_send.append(va)

                # lida com a logica de transferencia de combustivel
                if ab.operacao:
                    data_to_send.extend(transf_fuel(ab, mode="exclude"))

                # remove o registro de abastecimento
                db.session.delete(ab)
                message = 'Abastecimento excluído com sucesso!'

            # outras tabelas
            else:
                model = table_object(table_name=table_id)
                obj = db.session.query(model).get(request.form.get("id"))
                col_alteradas = ", ".join(f"({col.name})" for col in obj.__table__.columns)
                val_antigo = ", ".join(f"({getattr(obj, col.name)})" for col in obj.__table__.columns)
                history = PostoHistory(
                    id_reg=obj.id,
                    data_edicao=datetime.now(ZoneInfo("America/Sao_Paulo")).replace(microsecond=0),
                    user=current_user.username,
                    colunas_alteradas=col_alteradas,
                    valores_antigos=val_antigo
                )
                data_to_send.append(history)

                db.session.delete(obj)

        return send_data(data_to_send, collected_data, message)

    except Exception as e:
        db.session.rollback()
        return jsonify({'type': 'error', 'message': 'function error: ' + str(e)})


def process_form(form_id):
    try:
        data_to_send = []
        collected_data = None
        message = 'Dados enviados com sucesso!'

        # dados coletados baseados no id do formulario
        if form_id == "abastecimentos":
            collected_data = Abastecimentos(
                user=current_user.username,
                data_lanc=datetime.now(ZoneInfo("America/Sao_Paulo")).replace(microsecond=0),
                data_reg=datetime.strptime(request.form.get("data"), "%Y-%m-%d").date(),
                motorista=request.form.get("motorista"),
                placa=request.form.get("placa"),
                operacao=request.form.get("operacao") or None,
                observacoes=request.form.get("observacoes") or None,
                quilometragem=request.form.get("quilometragem") or None,
                volume=request.form.get("volume").replace(",", "."),
                cidade=request.form.get("cidade"),
                posto=request.form.get("posto"),
                odometro=request.form.get("odometro") or None,
                combustivel=request.form.get("combustivel") or None,
                preco=request.form.get("preco").replace(",", ".") or None
            )

        elif form_id == "entrega_combustivel":
            collected_data = EntregaCombustivel(
                user=current_user.username,
                data_lanc=datetime.now(ZoneInfo("America/Sao_Paulo")).replace(microsecond=0),
                data_reg=datetime.strptime(request.form.get("data"), "%Y-%m-%d").date(),
                volume=request.form.get("volume"),
                posto=request.form.get("posto"),
                odometro=request.form.get("odometro"),
                preco=request.form.get("preco").replace(",", ".")
            )

        # ajuste de posto para bombas
        if collected_data and "BOMBA" in collected_data.posto:
            odometro_atual = int(collected_data.odometro)

        # adiciona a sessão e garante ID
        db.session.add(collected_data)
        db.session.flush()

        # logica especifica de cada formulário
        if form_id == "entrega_combustivel":
            # cria ponto de virada
            pv = create_ponto_virada(collected_data)

            # atualiza volume atual
            va = VolumeAtual.query.filter_by(posto=collected_data.posto).first()
            if va:
                va.volume_restante = int(va.volume_restante) + float(collected_data.volume)
            else:
                va = VolumeAtual(
                    posto=collected_data.posto,
                    volume_restante=collected_data.volume
                )
                db.session.add(va)
            data_to_send.extend([collected_data, pv, va])

        elif form_id == "abastecimentos":
            if "BOMBA" in collected_data.posto:
                # atualiza preco pelo ponto de virada mais recente
                lanc_mais_prox = (
                    PontoVirada.query
                    .filter_by(posto=collected_data.posto)
                    .filter(PontoVirada.odometro_inicial <= int(collected_data.odometro))
                    .order_by(PontoVirada.id.desc())
                    .first()
                )
                if lanc_mais_prox:
                    collected_data.preco = lanc_mais_prox.preco

                # atualiza volume atual subtraindo o consumo
                va = VolumeAtual.query.filter_by(posto=collected_data.posto).first()
                if va:
                    va.volume_restante = int(va.volume_restante) - float(collected_data.volume)
                    data_to_send.extend([collected_data, va])
                else:
                    data_to_send.append(collected_data)

                # lida com a logica de transferencia de combustivel
                if collected_data.operacao:
                    data_to_send.extend(transf_fuel(collected_data, mode="new"))

        return send_data(data_to_send, collected_data, message)

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'type': 'error',
            'message': 'Ocorreu um erro, contate o administrador.',
            'error': str(e)
        })
