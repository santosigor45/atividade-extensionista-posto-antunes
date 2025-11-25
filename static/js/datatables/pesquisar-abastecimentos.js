$(document).ready(() => {
    // configura o moment.js com o formato de data especifico
    $.fn.dataTable.moment('DD/MM/YYYY HH:mm:ss');
    moment.locale('pt-br');

    // verifica se existe algum parametro passado na url
    const urlParams = new URLSearchParams(window.location.search);
    const searchFilter = urlParams.get('search[value]') || '';
    const searchStartDate = urlParams.get('startDate[value]') || '';
    const searchEndDate = urlParams.get('endDate[value]') || '';

    // escreve as datas da url nos campos
    if (searchStartDate) $('#start').val(searchStartDate);
    if (searchEndDate) $('#stop').val(searchEndDate);

    // inicializa a tabela
    const table = $('#table-abastecimentos').DataTable({
        lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]],
        ajax: {
            url: '/api/api_data/abastecimentos',
            data: (dtParms) => {
                // inclui parametros extras
                dtParms.minDate = $('#start').val();
                dtParms.maxDate = $('#stop').val();
                return dtParms;
            },
        },
        initComplete: function() {
            if (searchFilter) {
                this.api().search(searchFilter).draw();
            }
        },
        order: [[2, 'desc'], [0, 'desc']],
        processing: true,
        serverSide: true,
        language: {
            url: '/pt-BR.json'
        },
        columns: [
            { data: 'data_lanc', visible: false },
            {
                data: null,
                defaultContent: "",
                orderable: false,
                render: function (data, type, row) {
                    if (isEditor == true) {
                        return "<img src='/static/images/lapis.png' class='btn-edit' id='btn-edit' alt='icone_lapis'/>" +
                               "<img src='/static/images/lixeira.png' class='btn-edit' id='btn-delete' alt='icone_lixeira'/>";
                    }
                    return "<img src='/static/images/lapis.png' class='btn-edit btn-disabled' alt='icone_lapis'/>" +
                           "<img src='/static/images/lixeira.png' class='btn-edit btn-disabled' alt='icone_lixeira'/>";
                }
            },
            {
                data: 'data_reg',
                render: function (data, type, row) {
                    if (type === 'display' || type === 'filter') {
                        return moment.utc(data).locale('pt-br').format('L');
                    }
                    return data;
                }
            },
            { data: 'user' },
            { data: 'motorista' },
            { data: 'placa' },
            { data: 'observacoes' },
            { data: 'quilometragem', orderable: false },
            { data: 'volume' },
            { data: 'cidade' },
            { data: 'posto' },
            { data: 'odometro' },
            { data: 'combustivel' },
            { data: 'preco' },
        ],
    });

    // formata uma data no formato (DD/MM/YYYY)
    const formatDateToBrazilian = (dateStr) => {
        if (!dateStr) return '';

        const dateObj = new Date(dateStr);
        const day = String(dateObj.getDate()).padStart(2, '0');
        const month = String(dateObj.getMonth() + 1).padStart(2, '0');
        const year = dateObj.getFullYear();

        return `${day}/${month}/${year}`;
    };

    // evento para o botao de relatorio
    $('#report-button').on('click', () => {
        const searchTerm = table.search();
        const startDate = formatDateToBrazilian($('#start').val());
        const endDate = formatDateToBrazilian($('#stop').val());

        let reportTitle = 'Todos os Lançamentos';

        if (startDate && endDate) {
            reportTitle = (startDate === endDate)
                ? `Relatório do dia ${startDate}`
                : `Relatório de ${startDate} até ${endDate}`;
        }

        if (searchTerm) {
            reportTitle += ` (Busca: ${searchTerm})`;
        }

        if (!searchTerm && (!startDate || !endDate)) {
            const userConfirmed = confirm("Nenhum filtro selecionado. Isso irá imprimir todos os lançamentos existentes e pode demorar alguns minutos. Você tem certeza?");
            if (!userConfirmed) return;
        }

        const currentPageLength = table.page.len();

        // altera para exibir todas as entradas antes de imprimir
        table.page.len(-1).draw();

        table.one('draw', () => {
            table.buttons().destroy();
            new $.fn.dataTable.Buttons(table, {
                buttons: [
                    {
                        extend: 'print',
                        title: reportTitle,
                        exportOptions: {
                            columns: ':not(:first-child)'
                        },
                    }
                ]
            });

            table.button(0).trigger();

            // restaura o tamanho original da pagina após impressao
            setTimeout(() => {
                table.page.len(currentPageLength).draw();
            }, 500);
        });
    });

    // redesenha a tabela
    $('#start, #stop').on('change', () => {
        table.draw();
    });

    $('.btn-success').on('click', () => {
        setTimeout(() => {
            table.draw();
        }, 500);
    });

    // abre o modal de edicao
    $('#table-abastecimentos tbody').on('click', '#btn-edit', function () {
        const data = table.row($(this).closest('tr')).data();
        const dateTime = new Date(data.data_lanc);

        $('#editId').val(data.id);
        $('#editData').val(dateTime.toISOString().split("T")[0]);
        $('#editMotorista').val(data.motorista).trigger('change');
        $('#editPlaca').val(data.placa).trigger('change');
        $('input[name="operacao"][value="' + data.operacao + '"]').prop('checked', true);
        $('#editObservacoes').val(data.observacoes);
        $('#editQuilometragem').val(data.quilometragem);
        $('#editVolume').val(data.volume);
        $('#editCidade').val(data.cidade);
        $('#editPosto').val(data.posto);
        $('#editOdometro').val(data.odometro);
        $('#editCombustivel').val(data.combustivel);
        $('#editPreco').val(data.preco.replace('.', ','));
        $('#editModal').modal('show');
    });

    // abre o modal de exclusao
    $('#table-abastecimentos tbody').on('click', '#btn-delete', function () {
        const data = table.row($(this).closest('tr')).data();
        $('#deleteId').val(data.id);
        $('#deleteModal').modal('show');
    });
});
