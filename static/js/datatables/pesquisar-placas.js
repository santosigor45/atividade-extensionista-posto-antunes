$(document).ready(function () {
    // inicializa a tabela
    let table = $('#table-placas').DataTable({
        ajax: {
            url: '/api/api_data/placas',
        },
        order: [[7, 'desc'], [2, 'asc']],
        language: {
            url: '/pt-BR.json'
        },
        columns: [
            { data: 'id', visible: false },
            // coluna de acoes
            {
                data: null,
                defaultContent: "",
                className: 'actions-cell',
                orderable: false,
                render: function (data, type, row) {
                    if (isManager == true) {
                        return "<img src='/static/images/lapis.png' class='btn-edit' id='btn-edit' alt='icone_lapis'/>" +
                               "<img src='/static/images/lixeira.png' class='btn-edit' id='btn-delete' alt='icone_lixeira'/>";
                    }
                    return "<img src='/static/images/lapis.png' class='btn-edit btn-disabled' alt='icone_lapis'/>" +
                           "<img src='/static/images/lixeira.png' class='btn-edit btn-disabled' alt='icone_lixeira'/>";
                }
            },
            { data: 'placa' },
            { data: 'veiculo' },
            { data: 'modelo' },
            { data: 'qrcode' },
            { data: 'km_ideal' },
            // coluna ativo
            {
                data: 'ativo',
                render: function(data, type) {
                    if (type === 'sort') return data ? 1 : 0;
                    return data
                        ? "<input type='checkbox' checked disabled/>"
                        : "<input type='checkbox' disabled/>"
                },
            }
        ],

        // se o veiculo nao estiver ativo, aplica aspecto disabled a linha
        createdRow: function(row, data) {
            if (!data.ativo) {
                $(row).addClass('row-disabled');
            }
        },
    });

    // abre o modal de edicao
    $('#table-placas tbody').on('click', '#btn-edit', function () {
        let data = table.row($(this).parents('tr')).data();
        $('#editId').val(data.id);
        $('#editPlaca').val(data.placa);
        $('#editVeiculo').val(data.veiculo);
        $('#editModelo').val(data.modelo);
        $('#editQrcode').val(data.qrcode);
        $('#editKmideal').val(data.km_ideal);
        $('#editAtivo').prop('checked' ,data.ativo);
        $('#editModalLabel').text('Editar Placa');
        $('#editModal').modal('show');
    });

    // abre o modal de exclusao
    $('#table-placas tbody').on('click', '#btn-delete', function () {
        let data = table.row($(this).parents('tr')).data();
        $('#deleteId').val(data.id);
        $('#deleteModal').modal('show');
    });

    // abre o modal de cadastro
    $('#add-placa').on('click', function () {
        $('#editId').val(null);
        $('#editPlaca').val(null);
        $('#editVeiculo').val(null);
        $('#editQrcode').val(null);
        $('#editKmideal').val(0);
        $('#editAtivo').prop('checked' ,true);
        $('#editModalLabel').text('Cadastrar Placa');
        $('#editModal').modal('show');
    });

    // redesenha a tabela
    $('#reload-table').on('click', () => {
        table.ajax.reload();
    });

    // formata upper case no campo
    $('#editVeiculo, #editModelo').on('input', function () {
        $(this).val($(this).val().toUpperCase());
    });

    // remove o botao de cadastro se nao for manager
    if (isManager == false) {
        $('.div-cadastrar').addClass('hidden');
    };

    // aplica a formatacao de placa
    setupPlacaInput('editPlaca');
});