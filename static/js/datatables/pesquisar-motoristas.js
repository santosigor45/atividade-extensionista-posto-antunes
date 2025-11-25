$(document).ready(() => {
    // inicializa a tabela
    let table = $('#table-motoristas').DataTable({
        ajax: {
            url: '/api/api_data/motoristas',
        },
        language: {
            url: '/pt-BR.json'
        },
        columns: [
            { data: 'id', visible: false },
            {
                data: null,
                defaultContent: "",
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
            { data: 'motorista' },
            { data: 'cidade' }
        ],
    });

    // abre o modal de edicao
    $('#table-motoristas tbody').on('click', '#btn-edit', function () {
        let data = table.row($(this).parents('tr')).data();
        $('#editId').val(data.id);
        $('#editMotorista').val(data.motorista);
        $('#editCidade').val(data.cidade);
        $('#editModalLabel').text('Editar Motorista');
        $('#editModal').modal('show');
    });

    // abre o modal de cadastro
    $('#add-motorista').on('click', function () {
        $('#editId').val(null);
        $('#editMotorista').val(null);
        $('#editCidade').val(null);
        $('#editModalLabel').text('Incluir Motorista');
        $('#editModal').modal('show');
    });

    // abre o modal de exclusao
    $('#table-motoristas tbody').on('click', '#btn-delete', function () {
        let data = table.row($(this).parents('tr')).data();
        $('#deleteId').val(data.id);
        $('#deleteModal').modal('show');
    });

    // redesenha a tabela
    $('#reload-table').on('click', () => {
        table.ajax.reload();
    });

    // formata only letters no campo
    $('#editCidade, #editMotorista').on('input', function() {
        setupOnlyLetters(this.id);
    });

    // remove o botao de cadastro se nao for manager
    if (isManager == false) {
        $('.div-cadastrar').addClass('hidden');
    };
});