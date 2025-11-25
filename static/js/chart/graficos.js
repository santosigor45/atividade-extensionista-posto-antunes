// logica de graficos de abastecimentos

let abastecimentosChart = null;
let monthOffset = 0;
let customMode = false;

// elementos DOM
const prevBtn = document.getElementById('prevMonth');
const nextBtn = document.getElementById('nextMonth');
const customBtn = document.getElementById('customBtn');
const customInputs = document.getElementById('customInputs');

const monthLabel = document.getElementById('monthLabel');

const startInput = document.getElementById('startDate');
const endInput = document.getElementById('endDate');

const combSelect = document.getElementById('combSelect');
const metricSelect = document.getElementById('metricSelect');
const citySelect = document.getElementById('citySelect');
const printBtn = document.getElementById('printBtn');

Chart.register(ChartDataLabels);

// inicia apos o carregamento do DOM
document.addEventListener('DOMContentLoaded', () => {
    // navegacao por mes
    prevBtn.addEventListener('click', () => {
        if (customMode) return;
        monthOffset--;
        updateRange();
        loadData();
    });

    nextBtn.addEventListener('click', () => {
        if (customMode) return;
        monthOffset++;
        updateRange();
        loadData();
    });

    // alternar modo customizado
    customBtn.addEventListener('click', () => {
        customMode = !customMode;
        toggleCustom();
    });

    // recarrega os dados sempre que um filtro e alterado
    [combSelect, citySelect, metricSelect, startInput, endInput]
        .forEach(el => el.addEventListener('change', loadData));

    // carregamento inicial
    updateRange();
    loadData();

    // botao de impressao
    printBtn.addEventListener('click', printChart);
});

// calcula o mes atual de acordo com o valor de monthOffset
function updateRange() {
    const ref = new Date();
    ref.setMonth(ref.getMonth() + monthOffset);

    const first = new Date(ref.getFullYear(), ref.getMonth(), 1);
    const last = new Date(ref.getFullYear(), ref.getMonth() + 1, 0);

    startInput.value = first.toISOString().slice(0, 10);
    endInput.value = last.toISOString().slice(0, 10);

    monthLabel.textContent = ref.toLocaleDateString('pt-BR', {
        year: 'numeric',
        month: 'long'
    });
}

// visualizacao do input de date customizado
function toggleCustom() {
    customInputs.style.display = customMode ? 'block' : 'none';
    if (!customMode) {
        updateRange();
        loadData();
    }
}

// imprime o grafico
function printChart() {
    if (!abastecimentosChart) return;

    const imageURL = abastecimentosChart.toBase64Image();
    const summaryHTML = document.getElementById('chartSummary').outerHTML;


    const win = window.open('', '_blank');
    win.document.write(`
        <html>
          <head>
            <title>Imprimir Gráfico</title>
            <style>
              body { margin:0; padding:0; text-align:center; }
              img  { max-width:100%; height:auto; }
              #chartSummary { margin-top:12px; font-size:18px; font-family: system-ui; }
            </style>
          </head>
          <body>
            <img src="${imageURL}"/>
            ${summaryHTML}
          </body>
        </html>`);
    win.document.close();
    win.onload = () => {
        win.print();
        win.close();
    };
}

// atualiza o sumario
function updateSummary() {
    const ds = abastecimentosChart.data.datasets[0];
    const labels = abastecimentosChart.data.labels;

    // calculo de totais e medias
    const totalLiters   = ds._liters.reduce((sum, v) => sum + v, 0);
    const totalDistance = ds._distances
        ? ds._distances.reduce((sum, d) => sum + d, 0)
        : ds._liters.reduce((sum, l, i) => sum + l * ds.data[i], 0);
    const totalSpent    = ds._spent.reduce((sum, v) => sum + v, 0);
    const totalVehicles = labels.length;
    const avgKmLt       = totalLiters > 0 ? totalDistance / totalLiters : 0;

    // formatacao
    const fmtLiters = Math.round(totalLiters);
    const fmtAvg    = avgKmLt.toFixed(2);
    const fmtSpent  = totalSpent.toLocaleString('pt-BR', { minimumFractionDigits: 2 });

    // atualiza o HTML do sumario
    document.getElementById('chartSummary').innerHTML = `
        <span><strong>TOTAL DE VEÍCULOS:</strong> ${totalVehicles}</span>
        <div style="margin-top: 15px;">
            <span style="margin-right: 50px">
                <strong>LITRAGEM TOTAL:</strong> ${fmtLiters} Lts
            </span>
            <span style="margin-right: 50px">
                <strong>TOTAL GASTO:</strong> R$ ${fmtSpent}
            </span>
            <span>
                <strong>MÉDIA TOTAL:</strong> ${fmtAvg}
            </span>
        </div>
    `;
}

// carrega os dados
function loadData() {
    const params = new URLSearchParams({
        start: startInput.value,
        end: endInput.value,
        comb: combSelect.value,
        city: citySelect.value,
        metric: metricSelect.value
    });

    showLoading();
    fetch(`/api/chart_data?${params.toString()}`)
        .then(r => r.json())
        .then(renderChart)
        .catch(err => console.error('Erro ao carregar dados:', err))
        .finally(() => {
           hideLoading();
        });
}

// renderiza o grafico
function renderChart(data) {
    // define comportamentos de acordo com a metrica escolhida
    const metric = metricSelect.value;
    const showIdeal = metric === 'efficiency';
    const metricLabel = metric === 'efficiency' ? 'Eficiência (km/L)' : 'Volume (L)';
    const periodLabel = customMode
        ? `De ${startInput.value} a ${endInput.value}`
        : monthLabel.textContent;

    // acumula soma e contagem por modelo para posterior calculo de media
    const stats = {};
    data.forEach(d => {
        const key = d.veiculo;
        const value = metric === 'efficiency' ? d.distance / d.volume : d.volume;
        stats[key] = stats[key] || { sum: 0, count: 0 };
        stats[key].sum += value;
        stats[key].count += 1;
    });

    // calcula media por grupo de modelo em ordem crescente
    const models = Object.entries(stats)
        .map(([model, { sum, count }]) => ({ model, avg: sum / count }))
        .sort((a, b) => b.avg - a.avg);

    // distribui cores para cada grupo
    const n = models.length;
    const colors = {};
    models.forEach((m, i) => {
        const ratio = metric === 'efficiency' ? i / (n - 1) : (n - 1 - i) / (n - 1);
        const hue = 240 - 240 * ratio;
        colors[m.model] = `hsl(${hue},100%,50%)`;
    });

    /* agrupa em um unico array (flat) e armazena os indices de inicio e fim de cada grupo
    (groups) para facilitar anotacoes e legendas no grafico*/
    const flat = [];
    const groups = [];
    let idx = 0;
    models.forEach(({ model, avg }) => {
        const items = data.filter(d => d.veiculo === model);
        const startIdx = idx;
        items.forEach(it => { flat.push(it); idx++; });

        groups.push({
            model,
            startIndex: startIdx,
            endIndex:   idx - 1,
            avg
        });
    });

    // arrays
    const labels = flat.map(d => d.placa);
    const values = flat.map(d => metric === 'efficiency' ? +(d.distance / d.volume).toFixed(2) : d.volume);
    const spentVals = flat.map(d => d.spent);
    const literVals = flat.map(d => d.volume);
    const bgColors = flat.map(d => colors[d.veiculo]);
    const veiculosArr = flat.map(d => d.veiculo);
    const distanceVals = flat.map(d => d.distance);
    const modelsArr = flat.map(d => d.modelo);
    const minDates = flat.map(d => d.initial_date);
    const maxDates = flat.map(d => d.max_date);

    const idealVals = flat.map(d => d.km_ideal);
    const lowerVals = idealVals.map(v => +(v - 1).toFixed(2));
    const upperVals = idealVals.map(v => +(v + 1).toFixed(2));

    // box de km/lt ideal
    const annotations = {};
    if (showIdeal) {
        lowerVals.forEach((low, i) => {
            annotations[`box${i}`] = {
                type: 'box',
                xScaleID: 'x',
                yScaleID: 'y',
                xMin: i - 0.5,
                xMax: i + 0.5,
                yMin: low,
                yMax: upperVals[i],
                backgroundColor: 'rgba(0,0,255,0.1)',
                borderWidth: 0
            };
        });

        // linha de km/lt ideal
        idealVals.forEach((ideal, i) => {
            annotations[`line${i}`] = {
                type: 'line',
                xScaleID: 'x',
                yScaleID: 'y',
                xMin: i - 0.5,
                xMax: i + 0.5,
                yMin: ideal,
                yMax: ideal,
                borderColor: 'rgba(255,0,0,0.8)',
                borderWidth: 2,
                label: { enabled: false }
            };
        });
    }

    // se ja existe um grafico, destroi para recriar
    if (abastecimentosChart) abastecimentosChart.destroy();

    // instancia um novo grafico
    const ctx = document.getElementById('abastecimentosChart').getContext('2d');
    abastecimentosChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [
            {
                label: metricLabel,
                data: values,
                backgroundColor: bgColors,
                borderColor: 'rgba(0,0,0,1)',
                borderWidth: 1,
                order: 2,
                _origIdeal: idealVals.slice(),
                _origLower: lowerVals.slice(),
                _origUpper: upperVals.slice(),
                _origDistances: distanceVals.slice(),
                _minDates: minDates,
                _maxDates: maxDates,
                _metric: metric,
                _showIdeal: showIdeal,
                _spent: spentVals,
                _liters: literVals,
                _distances: distanceVals,
                _ideal: idealVals,
                _veiculos: veiculosArr,
                _plates: flat.map(d => d.placa),
                _models: modelsArr
            }]
        },
        options: {
            // muda cursor para pointer ao passar sobre uma barra
            onHover: (event, active) => {
                event.native.target.style.cursor = active[0] ? 'pointer' : 'default';
            },

            // ao clicar em uma barra, abre uma nova guia que mostra os abastecimentos daquela placa
            onClick: (evt, elements) => {
                if (!elements.length) return;
                const idx = elements[0].index;
                const ds = abastecimentosChart.data.datasets[0];
                const params = new URLSearchParams();
                params.set('search[value]', ds._plates[idx]);
                params.set('startDate[value]', ds._minDates[idx]);
                params.set('endDate[value]', ds._maxDates[idx]);
                window.open(`/pesquisar/abastecimentos?${params.toString()}`, '_blank');
            },

            // layout
            responsive: true,
            maintainAspectRatio: false,
            layout: { padding: { bottom: 40, top: 20 } },
            scales: {
                x: { ticks: { autoSkip: true, font: { size: 14 } } },
                y: { min: 0, beginAtZero: true }
            },

            // funcionalidades do grafico
            plugins: {
                // injeta as boxes e linhas de km/lt ideal
                annotation: {
                    annotations
                },

                // ajusta a logica do titulo de acordo com os filtros selecionados
                title: {
                    display: true,
                    color: '#000',
                    text: [`${metricLabel} — ${combSelect.value || 'Todos os combustíveis'}`,
                           `${citySelect.value || 'Todas as cidades'} — ${periodLabel}`],
                    font: { size: 32 },
                    padding: { bottom: 20 },
                },

                // legendas por modelo
                legend: {
                    position: 'top',
                    labels: {
                        font: { size: 14 },
                        boxWidth: 40,
                        generateLabels: chart => {
                            const ds = chart.data.datasets[0];
                            const models = [...new Set(ds._origModels || ds._veiculos)];
                            return models.map(model => ({
                                text: model,
                                fillStyle: (ds._origBgColors || ds.backgroundColor)[(ds._origModels || ds._veiculos).indexOf(model)],
                                hidden: ds._hiddenModels && ds._hiddenModels[model],
                                model
                            }));
                        }
                    },

                    /* ao clicar em uma legenda, esconde/mostra as barras daquele modelo e
                    reconfigura anotacoes e sumario*/
                    onClick: function(e, legendItem) {
                        const chart = this.chart;
                        const ds = chart.data.datasets[0];

                        // armazena dados originais na primeiza vez
                        if (!ds._origLabels) {
                            ds._origLabels = chart.data.labels.slice();
                            ds._origData = ds.data.slice();
                            ds._origBgColors  = ds.backgroundColor.slice();
                            ds._origSpent = ds._spent.slice();
                            ds._origLiters = ds._liters.slice();
                            ds._origModels = ds._veiculos.slice();
                            ds._origIdeal = ds._origIdeal.slice()
                            ds._origLower = ds._origLower.slice();
                            ds._origUpper = ds._origUpper.slice();
                            ds._origDistances = ds._origDistances.slice()
                            ds._hiddenModels = {};
                        }

                        // alterna o estado de oculto para o modelo clicado
                        const model = legendItem.text;
                        ds._hiddenModels[model] = !ds._hiddenModels[model];

                        // reconstroi arrays filtrando modelos ocultos
                        const newLabels = [];
                        const newData = [];
                        const newBg = [];
                        const newLiters = [];
                        const newSpent = [];
                        const newModels = [];
                        const newDistances = [];
                        const newIdeal = [];

                        ds._origModels.forEach((m, i) => {
                            if (ds._hiddenModels[m]) return;  // pula itens ocultos
                            newLabels.push(ds._origLabels[i]);
                            newData.push(ds._origData[i]);
                            newBg.push(ds._origBgColors[i]);
                            newSpent.push(ds._origSpent[i]);
                            newIdeal.push(ds._origIdeal[i]);
                            newDistances.push(ds._origDistances[i]);
                            newLiters.push(ds._origLiters[i]);
                            newModels.push(m);
                        });

                        // atualiza o dataset e labels do grafico
                        chart.data.labels = newLabels;
                        ds.data = newData;
                        ds.backgroundColor = newBg;
                        ds._liters = newLiters;
                        ds._spent = newSpent;
                        ds._distances = newDistances;
                        ds._ideal = newIdeal;
                        ds._veiculos = newModels;

                        // recria as boxes e lines para os indices que restaram
                        const newAnnos = {};
                        if (showIdeal) {
                            let annIdx = 0;
                            ds._origModels.forEach((m, origI) => {
                                if (ds._hiddenModels[m]) return;

                                // box
                                newAnnos[`box${annIdx}`] = {
                                    type: 'box',
                                    xScaleID: 'x',
                                    yScaleID: 'y',
                                    xMin: annIdx - 0.5,
                                    xMax: annIdx + 0.5,
                                    yMin: ds._origLower[origI],
                                    yMax: ds._origUpper[origI],
                                    backgroundColor: 'rgba(0,0,255,0.1)',
                                    borderWidth: 0
                                };
                                // line
                                newAnnos[`line${annIdx}`] = {
                                    type: 'line',
                                    xScaleID: 'x',
                                    yScaleID: 'y',
                                    xMin: annIdx - 0.5,
                                    xMax: annIdx + 0.5,
                                    yMin: ds._origIdeal[origI],
                                    yMax: ds._origIdeal[origI],
                                    borderColor: 'rgba(255,0,0,0.8)',
                                    borderWidth: 2,
                                    label: { enabled: false }
                                };
                                annIdx++;
                            });
                        }
                        // injeta no chart
                        chart.options.plugins.annotation.annotations = newAnnos;

                        // recalcula os grupos
                        const groups = [];
                        let idx = 0;
                        const stats = {};
                        newModels.forEach(m => {
                            if (!stats[m]) stats[m] = { start: idx, count: 0 };
                            stats[m].count++;
                            idx++;
                        });
                        for (const [model, { start, count }] of Object.entries(stats)) {
                            groups.push({ model, startIndex: start, endIndex: start + count - 1 });
                        }
                        chart.$groups = groups;

                        // redesenha o grafico e atualiza o sumario
                        chart.update();
                        updateSummary();
                    }
                },

                // rotulo acima de cada barra
                datalabels: {
                    anchor: 'end',
                    align: 'end',
                    color: '#000',
                    font: { weight: 'bold', size: 12 },

                    // alternancia para melhorar visualizacao com muitas barras
                    offset: c => (c.dataIndex % 2 === 0 ? 12 : 30)
                },

                // ao passar com o mouse, mostra uma box de informacoes sobre o veiculo
                tooltip: {
                    callbacks: {
                        label(ctx) {
                            const i = ctx.dataIndex;
                            const veiculo = ctx.dataset._veiculos[i];
                            const mdl = ctx.dataset._models[i];
                            const lines = [veiculo];

                            lines.push(`Modelo: ${mdl}`)

                            if (metric === 'efficiency') {
                                lines.push(``);
                                lines.push(`Eficiência: ${ctx.raw} km/lt`);
                                lines.push(`Ideal: ${ctx.dataset._ideal[i]} km/lt`);
                                lines.push(``);
                                lines.push(`Volume: ${ctx.dataset._liters[i]} litros`);
                            } else {
                                lines.push(`Volume: ${ctx.raw} L`);
                            }

                            lines.push(`Gasto: R$ ${ctx.dataset._spent[i]
                                .toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`);
                            lines.push(`KM Rodado: ${ctx.dataset._distances[i]} km`);
                            return lines;
                        }
                    }
                }
            }
        },
        plugins: [ChartDataLabels]
    });

    abastecimentosChart.$groups = groups;

    updateSummary();
}
