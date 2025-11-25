from flask import request, jsonify, abort
from collections import defaultdict
from datetime import datetime, timedelta, time, date
from calendar import monthrange
from math import ceil
from flask_login import current_user
from models import db, Placas, Abastecimentos, EntregaCombustivel, table_object


def chart_data():
    """
    Return JSON data for abastecimentos chart, filtered by date, fuel type, and city.
    Supports 'volume' and 'efficiency' metrics.
    Optimized to perform a single query for all relevant records.
    """
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    comb = request.args.get('comb')
    city = request.args.get('city')
    metric = request.args.get('metric', 'volume')

    if start_str:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        start_dt = datetime.combine(start_date, time.min)
    else:
        start_date = None
        start_dt = None

    if end_str:
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        end_dt = datetime.combine(end_date + timedelta(days=1), time.min)
    else:
        end_date = None
        end_dt = None

    placa_query = (
        db.session.query(
            Abastecimentos.placa,
            Placas.veiculo,
            Placas.modelo,
            Placas.km_ideal
        )
        .join(Placas, Abastecimentos.placa == Placas.placa)
        .filter(Abastecimentos.placa != 'SEM-PLACA')
    )

    if start_dt and end_dt:
        placa_query = placa_query.filter(
            Abastecimentos.data_reg >= start_dt,
            Abastecimentos.data_reg < end_dt
        )

    if comb:
        placa_query = placa_query.filter(
            Abastecimentos.combustivel.ilike(f"%{comb}%")
        )

    if city:
        placa_query = placa_query.filter(
            Abastecimentos.cidade.ilike(f"%{city}%")
        )

    placa_objs = (
        placa_query
        .group_by(Abastecimentos.placa, Placas.veiculo, Placas.modelo, Placas.km_ideal)
        .all()
    )

    placas = [p.placa for p in placa_objs]
    veiculo_map = {p.placa: p.veiculo for p in placa_objs}
    modelo_map = {p.placa: p.modelo for p in placa_objs}
    km_ideal_map = {p.placa: p.km_ideal for p in placa_objs}

    if not placas:
        return jsonify([])

    recs_query = db.session.query(Abastecimentos).filter(Abastecimentos.placa.in_(placas))
    if end_dt:
        recs_query = recs_query.filter(Abastecimentos.data_reg < end_dt)
    recs_all = (
        recs_query
        .order_by(Abastecimentos.placa, Abastecimentos.data_reg)
        .all()
    )

    grouped = defaultdict(list)
    for rec in recs_all:
        grouped[rec.placa].append(rec)

    data = []
    for placa in placas:
        recs = grouped.get(placa, [])
        if not recs:
            continue

        recs_by_date = [
            ((r.data_reg.date() if isinstance(r.data_reg, datetime) else r.data_reg), r)
            for r in recs
        ]

        if metric == 'efficiency':
            if start_date and len(recs_by_date) == 1 and recs_by_date[0][0] < start_date:
                continue

            if start_date:
                prev_end = start_date.replace(day=1) - timedelta(days=1)
                prev_start = prev_end.replace(day=1)
            else:
                prev_start = prev_end = None

            before = [r for dt, r in recs_by_date if prev_start and prev_end and prev_start <= dt <= prev_end]
            period = [r for dt, r in recs_by_date if start_date and end_date and start_date <= dt <= end_date]

            if before:
                init = before[-1]
                initial_km = init.quilometragem
                initial_vol = init.volume
                initial_spent = initial_vol * init.preco
            elif period:
                init = period[0]
                initial_km = init.quilometragem
                initial_vol = 0
                initial_spent = 0
            else:
                continue

            final = period[-1]
            final_km = final.quilometragem

            vols = [r.volume for r in period[:-1]] if len(period) > 1 else []
            spent = [r.volume * r.preco for r in period[:-1]] if len(period) > 1 else []

            total_vol = initial_vol + sum(vols)
            total_spent = initial_spent + sum(spent)
            total_dist = final_km - initial_km

            if total_vol > 0 and total_dist > 0:
                init_date = init.data_reg.isoformat()
                max_date = final.data_reg.isoformat()

                data.append({
                    'placa': placa,
                    'veiculo': veiculo_map[placa],
                    'modelo': modelo_map[placa],
                    'km_ideal': float(km_ideal_map[placa]),
                    'volume': float(total_vol),
                    'distance': float(total_dist),
                    'spent': float(total_spent),
                    'initial_date': init_date,
                    'max_date': max_date
                })
        else:
            if start_date:
                period_recs = [r for dt, r in recs_by_date if dt >= start_date]
            else:
                period_recs = [r for _, r in recs_by_date]

            total_vol = sum(r.volume for r in period_recs)
            kms = [r.quilometragem for r in period_recs]
            total_spent = sum(r.volume * r.preco for r in period_recs)

            if total_vol > 0 and kms:
                init = period_recs[0]
                end = period_recs[-1]
                data.append({
                    'placa':   placa,
                    'veiculo': veiculo_map[placa],
                    'modelo': modelo_map[placa],
                    'volume': float(total_vol),
                    'distance': float(max(kms) - min(kms)),
                    'spent': float(total_spent),
                    'initial_date': init.data_reg.isoformat(),
                    'max_date': end.data_reg.isoformat()
                })

    if metric == 'efficiency':
        key_fn = lambda x: x['distance'] / x['volume']
    else:
        key_fn = lambda x: x['volume']
    data.sort(key=key_fn, reverse=True)

    return jsonify(data)


def api_data(data):
    if data in ["placas", "motoristas"]:
        return {
            "data": [row.to_dict() for row in db.session.query(table_object(table_name=data))],
        }

    query = db.session.query(table_object(table_name=data))

    # date range filter
    min_date = request.args.get("minDate")
    max_date = request.args.get("maxDate")
    if min_date and max_date:
        query = query.filter(db.and_(
            db.func.date(table_object(table_name=data).data_reg) >= min_date,
            db.func.date(table_object(table_name=data).data_reg) <= max_date
        ))

    # user filter
    if not (current_user.is_admin or current_user.is_manager):
        query = query.filter_by(user=current_user.username)

    # search filter
    search = request.args.get("search[value]")

    if search:
        search_str = str(search).strip()
        if data == "abastecimentos":
            query = query.filter(db.or_(
                Abastecimentos.data_reg.icontains(search_str),
                Abastecimentos.user.icontains(search_str),
                Abastecimentos.motorista.icontains(search_str),
                Abastecimentos.placa.icontains(search_str),
                Abastecimentos.observacoes.icontains(search_str),
                Abastecimentos.volume.icontains(search_str),
                Abastecimentos.cidade.icontains(search_str),
                Abastecimentos.posto.icontains(search_str),
                Abastecimentos.combustivel.icontains(search_str),
                Abastecimentos.preco.icontains(search_str)
            ))

        elif data == "entrega_combustivel":
            query = query.filter(db.or_(
                EntregaCombustivel.data_reg.icontains(search_str),
                EntregaCombustivel.user.icontains(search_str),
                EntregaCombustivel.posto.icontains(search_str),
                EntregaCombustivel.volume.icontains(search_str),
                EntregaCombustivel.preco.icontains(search_str)
            ))

    total_filtered = query.count()

    # sorting
    order = []
    i = 0
    while True:
        col_index = request.args.get(f"order[{i}][column]")
        if col_index is None:
            break
        col_name = request.args.get(f"columns[{col_index}][data]")
        if data == "abastecimentos":
            if col_name not in ["data_reg", "data_lanc", "user", "motorista", "placa", "quilometragem", "volume", "cidade",
                                "posto", "odometro", "combustivel"]:
                col_name = "name"
            col = getattr(Abastecimentos, col_name)
        elif data == "entrega_combustivel":
            if col_name not in ["data_reg", "data_lanc", "user", "posto", "volume", "odometro", "preco"]:
                col_name = "name"
            col = getattr(EntregaCombustivel, col_name)
        descending = request.args.get(f"order[{i}][dir]") == "desc"
        if descending:
            col = col.desc()
        order.append(col)
        i += 1
    if order:
        query = query.order_by(*order)

    # pagination
    start = request.args.get("start", type=int)
    length = request.args.get("length", type=int)

    if length == -1:
        final_query = query.offset(start)
    else:
        final_query = query.offset(start).limit(length)

    # response
    return {
        "data": [row.to_dict() for row in final_query],
        "recordsFiltered": total_filtered,
        "recordsTotal": query.count(),
        "draw": request.args.get("draw", type=int),
    }


def validate_mileage(placa, km):
    try:
        query = Abastecimentos.query.filter_by(placa=placa).order_by(
            Abastecimentos.id.desc()).first()

        if query:
            result = (query.quilometragem + 3000) > int(km) > query.quilometragem

            if result:
                message = "Ok!"
                return jsonify({'message': f'{message}', 'result': result})
            else:
                message = "Por favor, digite o KM novamente!"
                return jsonify({'message': f'{message}', 'result': result})

        else:
            message = "Nenhum registro encontrado!"
            return jsonify({'message': f'{message}', 'result': True})

    except Exception as e:
        abort(500, description=str(e))


def validate_odometer(posto, odometro, form_id):
    try:
        posto = posto
        query = None
        max_range = 3000

        if form_id == "abastecimentos":
            query = Abastecimentos.query.filter_by(posto=posto).order_by(
                Abastecimentos.id.desc()).first()

        elif form_id == "entrega_combustivel":
            query = EntregaCombustivel.query.filter_by(posto=posto).order_by(
                EntregaCombustivel.id.desc()).first()
            max_range = 10000

        if query:
            result = (query.odometro + max_range) > int(odometro) > query.odometro

            if result:
                message = "Ok!"
                return jsonify({'message': f'{message}', 'result': result})

            else:
                message = "Por favor, digite o odômetro novamente!"
                return jsonify({'message': f'{message}', 'result': result})

        else:
            message = "Nenhum registro encontrado!"
            return jsonify({'message': f'{message}', 'result': True})

    except Exception as e:
        abort(500, description=str(e))


def validate_qrcode(qrcode):
    try:
        query = Placas.query.filter_by(qrcode=qrcode).first()

        if query:
            message = "Ok!"
            return jsonify({'message': f'{message}', 'placa': query.placa})

        else:
            message = "QR Code ainda não cadastrado. Digite a placa manualmente."
            return jsonify({'message': f'{message}', 'placa': None})

    except Exception as e:
        abort(500, description=str(e))
