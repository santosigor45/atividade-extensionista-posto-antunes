// dispara quando a página ainda estiver carregando
window.addEventListener('beforeunload', showLoading);

// dispara quando o DOM estiver completamente carregado
document.addEventListener('DOMContentLoaded', function () {
    hideLoading();
    updateDate();
    showModal();
    showCustomMessage();
    setupFormListeners();
    setupPlacaInput();
    setupSendButtonBehavior();

    // captura invalid de qualquer elemento, aplicando focus
    document.addEventListener('invalid', function(e){
        $(e.target).focus();
    }, true);

    // event listener de foco para qualquer elemento, ativando a função scrollToView
    $(document).on('focusin', scrollToView);
});

// dispara quando o usuario retornar a pagina anterior
window.addEventListener('pageshow', hideLoading);

/*************************************************************/
/*                   ENVIO DE FORMULARIO                     */
/*************************************************************/

// inicializa listeners em todos os formulários (edit, delete, dados)
function setupFormListeners() {
    document.querySelectorAll('form.edit, form.delete, form.dados').forEach(function (form) {
        form.addEventListener('submit', async function (event) {
            event.preventDefault();
            const formData = new FormData(this);
            const formId = form.getAttribute('id');

            const url = '/process_form/' +
                        (formId.startsWith('edit') ? 'edit/' :
                        formId.startsWith('delete') ? 'delete/' : 'send/') +
                        formId;

            // regras de validacao
            let isValid = true;

            if (formId === 'abastecimentos') {
                isValid = await validateMileage() && await validateOdometer(formId);
            } else if (formId === 'entrega_combustivel') {
                isValid = await validateOdometer(formId);
            }

            if (isValid) {
                submitFormData(url, formData, form, formId);
            }
        });
    });
}


// envia dados do formulário ao servidor e lida com a resposta
function submitFormData(url, formData, form, formId) {
    showLoading();
    sendDataToServer(url, formData, form.getAttribute('method'))
        .then(({ message, type, error }) => {
            if (url.includes('send')) {
                formReset(formId);
            } else {
                $('.modal').modal('hide');
                $('#reload-table').click();
            }
            hideLoading();
            showFlashMessage(message, type);

            if (error) {
                console.log(error);
            }
        })
        .catch(error => {
            if (url.includes('send')) {
                showFlashMessage('Houve um erro. Por favor, verifique a conexão e tente novamente.', 'info');
            } else {
                $('.modal').modal('hide');
                showFlashMessage('Houve um erro. Por favor, verifique a conexão e tente novamente.', 'error');
            }
            console.log(error);
        });
}


// requisicao generica ao servidor, usando fetch
function sendDataToServer(url, formData, method = 'POST') {
    if (method === 'GET') {
        return fetch(url, { method }).then((response) => response.json());
    }
    return fetch(url, { method, body: formData }).then((response) => response.json());
}

/*************************************************************/
/*               CONFIGURAÇÕES DE FORMULÁRIO                 */
/*************************************************************/

// atualiza o campo de data para a data atual no formato ISO (yyyy-mm-dd)
function updateDate() {
    var today = new Date();
    var offset = today.getTimezoneOffset() * 60000;
    var localISOTime = (new Date(today - offset)).toISOString().split('T')[0];
    dataElement = document.getElementById('data')
    if (dataElement) {
        dataElement.value = localISOTime;
    }
}


// configura campo de input para placa, exibindo opções filtradas e formatando a digitacao
function formatarPlaca(valor) {
    let v = valor.toUpperCase();

    if (v === 'SEM-PLACA') {
        return 'SEM-PLACA';
    }

    if (v.length <= 3) {
        v = v.replace(/[^A-Z]/g, '');
    }
    else if (v.length === 4) {
        if (v.charAt(3) !== '-' && /[0-9]/.test(v.charAt(3))) {
            v = v.substring(0,3) + '-' + v.charAt(3);
        } else {
            v = v.slice(0,3);
        }
    }
    else if (v.length === 6) {
        let parte1 = v.substring(0,5);
        let c5 = v.charAt(5).replace(/[^A-J0-9]/g, '');
        v = parte1 + c5;
    }
    else if (v.length >= 7) {
        let p0 = v.substring(0,6);
        let c6 = v.charAt(6).replace(/[^0-9]/g, '');
        let c7 = v.charAt(7).replace(/[^0-9]/g, '');
        v = p0 + c6 + c7;
    }

    return v;
}

function bindPlacaEvents(el) {
    $(el).off('input.placa').on('input.placa', function(){
        this.value = formatarPlaca(this.value);
    });
    $(el).off('keydown.placa').on('keydown.placa', function(e){
        if (e.key === 'Backspace' && this.value.length === 5) {
            this.value = this.value.slice(0,-1);
        }
    });
}

function setupPlacaInput(fieldId = 'placa') {
    const el = document.getElementById(fieldId);
    if (!el) return;
    bindPlacaEvents(el);
}

$('#placa, #editPlaca').on('select2:open', function(){
    const $search = $('.select2-search__field');
    bindPlacaEvents($search[0]);
});


// formata valor monetario no campo de preco
function setupPrecoInput(e, field = 'preco') {
    var x = document.getElementById(field);
    var currentVal = x.value;

    document.getElementById(field).addEventListener('input', function (e) {
        this.value = this.value.replace(/[^0-9]/g, '');
    });

    if (currentVal == "") {
        x.value = "0,00";
    } else {
        var num = currentVal.replace(/,/g, '').replace(/^0+/, '');
        if(num == "") num = "0";
        var len = num.length;
        if(len == 1) num = "0,0" + num;
        else if(len == 2) num = "0," + num;
        else num = num.slice(0, len-2) + "," + num.slice(len-2);
        x.value = num;
    }
}

// desabilita o botao de envio por um curto período para evitar envios duplicados
function setupSendButtonBehavior() {
    const submitButton = document.getElementById('enviar-btn');
    const formFields = document.querySelectorAll('input, select');

    if (!submitButton) return;

    submitButton.addEventListener('click', () => {
        setTimeout(() => {
            addRemoveDisabled(['enviar-btn'], ['add']);
        }, 100);
    });

    formFields.forEach((field) => {
        field.addEventListener('input', () => {
            addRemoveDisabled(['enviar-btn'], ['remove']);
        });
    });
}

/*************************************************************/
/*                VERIFICAÇÕES DE FORMULÁRIO                 */
/*************************************************************/

// variaveis permanentes para armazenar o ultimo par de placa e quilometragem e o contador
let lastPlaca = null;
let lastKm = null;
let contadorMileage = 0;

// verifica a quilometragem inserida de forma assincrona
async function validateMileage() {
    const placa = document.getElementById('placa').value.trim();
    const kmField = document.getElementById('quilometragem');
    const km = kmField.value.trim();

    if (placa === 'SEM-PLACA') {
        return true;
    }

    const isSamePair = (placa === lastPlaca) && (km === lastKm);

    if (!isSamePair) {
        lastPlaca = placa;
        lastKm = km;
        contadorMileage = 0;
    }

    if (isSamePair && contadorMileage > 1) {
        console.log('Validação ignorada. Liberando envio automaticamente.');
        return true;
    }

    try {
        const serverAvailable = await checkServerAvailability();
        if (serverAvailable) {
            try {
                const { message, result } = await sendDataToServer(
                    `/api/validate_mileage/${encodeURIComponent(placa)}/${encodeURIComponent(km)}`,
                    null,
                    'GET'
                );

                if (!result) {
                    contadorMileage++;

                    if (contadorMileage > 1) {
                        console.warn('Contador excedido. Liberando envio apesar da validação falhar.');
                        return true;
                    }

                    showFlashMessage(message, 'info');
                    kmField.value = '';
                    kmField.focus();
                    setTimeout(() => {
                        addRemoveDisabled(['enviar-btn'], ['remove']);
                    }, 1000);
                    return false;
                }

                return true;

            } catch (error) {
                console.error('Erro ao enviar dados ao servidor:', error);
                return true;
            }
        } else {
            console.warn('Servidor indisponível. Permitindo operação como fallback.');
            return true;
        }
    } catch (error) {
        console.error('Erro ao verificar disponibilidade do servidor:', error);
        return true;
    }
}


// variaveis permanentes para armazenar o ultimo par de posto, odometro e o contador
let lastPosto = null;
let lastOdometer = null;
let contadorOdometer = 0;

// verifica o odômetro inserido de forma assincrona
async function validateOdometer(formId) {
    const posto = document.getElementById('posto').value.trim();
    const odometerField = document.getElementById('odometro');
    const odometro = odometerField.value.trim();

    if (!posto.includes('BOMBA')) {
        return true;
    }

    const isSameCombination = (posto === lastPosto) && (odometro === lastOdometer);

    if (!isSameCombination) {
        lastPosto = posto;
        lastOdometer = odometro;
        contadorOdometer = 0;
    }

    if (isSameCombination && contadorOdometer > 1) {
        console.log('Validação ignorada. Liberando envio automaticamente.');
        return true;
    }

    try {
        const serverAvailable = await checkServerAvailability();
        if (serverAvailable) {
            try {
                const { message, result } = await sendDataToServer(
                    `/api/validate_odometer/${
                    encodeURIComponent(posto)}/${
                    encodeURIComponent(odometro)}/${
                    encodeURIComponent(formId)}`,
                    null,
                    'GET'
                );

                if (!result) {
                    contadorOdometer++;

                    if (contadorOdometer > 1) {
                        console.warn('Contador excedido. Liberando envio apesar da validação falhar.');
                        return true;
                    }

                    showFlashMessage(message, 'info');
                    odometerField.value = '';
                    odometerField.focus();
                    setTimeout(() => {
                        addRemoveDisabled(['enviar-btn'], ['remove']);
                    }, 1000);
                    return false;
                }

                return true;

            } catch (error) {
                console.error('Erro ao enviar dados ao servidor:', error);
                return true;
            }
        } else {
            console.warn('Servidor indisponível. Permitindo operação como fallback.');
            return true;
        }
    } catch (error) {
        console.error('Erro ao verificar disponibilidade do servidor:', error);
        return true;
    }
}


// ajusta campo de preco, combustivel e odometro dependendo do posto selecionado
function validateStationName() {
    var valorSelecionado = document.getElementById("posto").value;

    if (valorSelecionado.toLowerCase().includes("bomba")) {
        document.getElementById("div-preco").style.display = "none";
        document.getElementById("div-combustivel").style.display = "none";
        document.getElementById("combustivel").selectedIndex = 1;
        document.getElementById("combustivel").required = false;
        document.getElementById("div-odometro").style.display = "block";
        document.getElementById("odometro").required = true;
    } else {
        document.getElementById("div-preco").style.display = "flex";
        document.getElementById("div-combustivel").style.display = "block";
        document.getElementById("combustivel").selectedIndex = 0;
        document.getElementById("combustivel").required = true;
        document.getElementById("div-odometro").style.display = "none";
        document.getElementById("odometro").required = false;
    }
}


// formata o texto digitado em um campo de placa (AAA-0A00)
function validateLicensePlate(placa_id, km_id) {
    var placaElement = document.getElementById(placa_id);
    var kmElement = document.getElementById(km_id);
    if (placaElement.value == "SEM-PLACA") {
        kmElement.required = false;
        document.getElementById("div-observacoes").style.display = "block";
        document.getElementById("btn-rg").required = true;
    } else {
        kmElement.required = true;
        document.getElementById("div-observacoes").style.display = "none";
        document.getElementById("btn-rg").required = false;
    }
}

/*************************************************************/
/*                        ESTÉTICA                           */
/*************************************************************/

// faz a rolagem suave ate o elemento focado com um atraso
function scrollToView(event) {
    let activeElement = event.target;
    setTimeout(() => {
        activeElement.scrollIntoView({behavior: 'smooth', block: 'center'});
    }, 300);
}


// exibe saudacao personalizada (bom dia, boa tarde, boa noite)
function showCustomMessage() {
    let hora = new Date().getHours();
    let mensagem = hora < 12 ? "Bom dia, " : hora < 18 ? "Boa tarde, " : "Boa noite, ";
    let $mensagem = $("#welcome-message");
    if ($mensagem.length) {
        $mensagem.html(mensagem + $mensagem.html());
    }
}

/*************************************************************/
/*                        MODALS                             */
/*************************************************************/

// abre o modal
function showModal() {
    var modal = document.getElementById('myModal');
    var flashes = document.querySelector('.flashes');
    if (flashes && flashes.children.length > 0) {
        modal.classList.add('show');
        setTimeout(function () {
            closeModal(modal.getAttribute("id"));
        }, 3000);
        window.addEventListener('click', function (event) {
            if (event.target === modal) {
                closeModal(modal.getAttribute("id"));
            }
        });
    }
}


// fecha o modal
function closeModal(modal_id) {
    var modal = document.getElementById(modal_id);
    modal.classList.add('fade-out');
    setTimeout(function () {
        modal.classList.remove('show', 'fade-out');
    }, 200);
}


// gerencia mensagens flash em uma modal
function showFlashMessage(mensagem, tipo) {
    var modal = document.getElementById('jsModal');
    modal.classList.add('show');
    var flash_content = document.getElementById('js-flash-content');
    var flash_text = document.getElementById('js-flash-text');
    flash_text.classList.add("flash-text-" + tipo);
    flash_content.classList.add("flash-" + tipo);
    flash_text.innerHTML = mensagem;
    setTimeout(function () {
        flash_text.classList.remove("flash-text-" + tipo);
        flash_content.classList.remove("flash-" + tipo);
        closeModal(modal.getAttribute("id"));
    }, 3000);
    window.addEventListener('click', function (event) {
        if (event.target === modal) {
            closeModal(modal.getAttribute("id"));
        }
    });
}

/*************************************************************/
/*                     QR CODE SCANNER                       */
/*************************************************************/

// Responsável por manter a instância ativa do scanner de QR code
let qrScanner;


// Exibe o modal, configura o vídeo e inicia a captura de QR codes usando a câmera traseira
function startQrScanner() {
    $('#readerModal').modal('show');

    $('#readerModal')
        .off('shown.bs.modal.myScan')
        .on('shown.bs.modal.myScan', () => {
            const video = document.getElementById('reader');
            video.srcObject = null;

            if (qrScanner) {
                qrScanner.stop();
                qrScanner.destroy();
                qrScanner = null;
            }

            qrScanner = new QrScanner(
                video,
                result => {
                    const decodedText = typeof result === 'string'
                        ? result
                        : (result.data ?? result.rawValue ?? '');
                    onScanSuccess(decodedText);
                },
                {
                    highlightScanRegion: true,
                    highlightCodeOutline: true,
                    preferredCamera: 'environment'
                }
            );

            qrScanner.start().catch(err => {
                console.error('qr-scanner erro:', err);
                alert(err);
                $('#readerModal').modal('hide');
            });
        });
}


// Ao fechar o modal, para qualquer captura em andamento e libera recursos do scanner
$('#readerModal').on('hide.bs.modal', () => {
    if (qrScanner) {
        qrScanner.stop();
        qrScanner.destroy();
        qrScanner = null;
    }
});


// Recebe o texto decodificado, verifica o qrcode e retorna a placa
async function onScanSuccess(decodedText) {

    const overlay = document.getElementById('qrSuccessOverlay');

    qrScanner.stop();

    setTimeout(async () => {
        overlay.classList.add('show');
    }, 200)

    setTimeout(async () => {
        $('#readerModal').modal('hide');
        overlay.classList.remove('show');
    }, 800)

    showLoading();

    try {
        const serverAvailable = await checkServerAvailability();
        if (serverAvailable) {
            try {
                if ($('#placa').length) {
                    const { message, placa } = await sendDataToServer(
                        `/api/validate_qrcode/${encodeURIComponent(decodedText)}`,
                        null,
                        'GET'
                    );
                    if (placa) {
                        $('#placa').val(placa).trigger('change');
                    } else {
                        $('#placa').val('').trigger('change');
                        showFlashMessage(message, 'info');
                    }
                } else if ($('#editQrcode').length) {
                    const { message, placa } = await sendDataToServer(
                        `/api/validate_qrcode/${encodeURIComponent(decodedText)}`,
                        null,
                        'GET'
                    );
                    if (placa) {
                        if ($('#editPlaca').val() == placa) {
                            showFlashMessage('QR Code já vinculado a esta placa.', 'info');
                        } else {
                            showFlashMessage('QR Code já vinculado a outra placa.', 'info');
                        }
                    } else {
                        $('#editQrcode').val(decodedText);
                    }
                }

            } catch (error) {
                console.error('Erro ao enviar dados ao servidor:', error);
            }
        } else {
            console.warn('Servidor indisponível.');
        }
    } catch (error) {
        console.error('Erro ao verificar disponibilidade do servidor:', error);
    } finally {
        hideLoading();
    }
}

/*************************************************************/
/*                        UTILIDADES                         */
/*************************************************************/

// verifica disponibilidade do servidor atraves da rota /ping
function checkServerAvailability() {
    return fetch('/ping')
        .then(response => response.ok ? true : false)
        .catch(() => false);
}


// converte um objeto FormData para um objeto JS simples (key-value)
function formDataToObject(formData) {
    var formDataObject = {};
    formData.forEach(function(value, key){
        formDataObject[key] = value;
    });
    return formDataObject;
}


// exibe caixa de dialogo de confirmacao para limpeza de formulario
function confirmFormReset(form) {
    var confirmar = confirm("Tem certeza que deseja limpar tudo?");
    if (confirmar) {
        formReset(form);
    }
}


// reseta o formulario e atualiza a data para o dia atual
function formReset(formId) {
    var form = document.getElementById(formId);
    form.reset();
    updateDate();

    $(form).find('select').each(function() {
        var $this = $(this);
        if ($this.data('select2')) {
            $this.val(null).trigger('change');
        }
    });
}


// funcao generica que formata o input apenas com letras
function setupOnlyLetters(idElement) {
    element = document.getElementById(idElement);
    element.value = element.value.toUpperCase().replace(/[0-9]/g, '');
}

// controla a propriedade disabled em elementos
function addRemoveDisabled(element, option) {
    var elementControlled = []
    for (var i = 0; i < element.length; i++) {
        elementControlled[i] = document.getElementById(element[i]);

        if (option.length <= 1) {
            if (option == 'add') {
                elementControlled[i].disabled = true;
            } else if (option == 'remove') {
                elementControlled[i].disabled = false;
            }
        } else {
            if (option[i] == 'add') {
                elementControlled[i].disabled = true;
            } else if (option[i] == 'remove') {
                elementControlled[i].disabled = false;
            }
        }
    }
}

// Exibe o overlay de loading
function showLoading() {
  document.getElementById('globalLoadingOverlay')
          .style.display = 'flex';
}

// Esconde o overlay de loading
function hideLoading() {
  document.getElementById('globalLoadingOverlay')
          .style.display = 'none';
}
