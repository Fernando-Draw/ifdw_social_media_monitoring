odoo.define('smmonitor.graph_analytics', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;

    var AnalyticsGraphSmmonitor = AbstractAction.extend({
        template: 'AnalyticsGraphSmmonitorTemplate',

        start: function () {
            this._super.apply(this, arguments);
            this.renderDashboard();
        },

        renderDashboard: function () {
            this.$el.html(QWeb.render('AnalyticsGraphSmmonitorTemplate'));
            applyDateFilter();  // Inicializa con datos filtrados si es necesario
        },
    });

    AnalyticsGraphSmmonitor.template = "AnalyticsGraphSmmonitorTemplate";
    registry.category("actions").add("analytics_graph_smmonitor", AnalyticsGraphSmmonitor);

    function renderCharts(data) {
        var ctxBar = document.getElementById('barChart').getContext('2d');
        var ctxLine = document.getElementById('lineChart').getContext('2d');

        // Configuración del gráfico de barras
        var barChart = new Chart(ctxBar, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [
                    { label: 'Engagement', backgroundColor: '#FF6384', data: data.engagement },
                    { label: 'Interactions', backgroundColor: '#36A2EB', data: data.interactions },
                    { label: 'Reach', backgroundColor: '#FFCE56', data: data.reach },
                    { label: 'Impressions', backgroundColor: '#4BC0C0', data: data.impressions }
                ]
            },
        });

        // Configuración del gráfico de líneas
        var lineChart = new Chart(ctxLine, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [
                    { label: 'Engagement', borderColor: '#FF6384', data: data.engagement, fill: false, tension: 0.4 },
                    { label: 'Interactions', borderColor: '#36A2EB', data: data.interactions, fill: false, tension: 0.4 },
                    { label: 'Reach', borderColor: '#FFCE56', data: data.reach, fill: false, tension: 0.4 },
                    { label: 'Impressions', borderColor: '#4BC0C0', data: data.impressions, fill: false, tension: 0.4 }
                ]
            }
        });
    }

    function applyDateFilter() {
        var startDate = document.getElementById('start_date').value;
        var endDate = document.getElementById('end_date').value;

        ajax.jsonRpc('/smmonitor/get_filtered_data', 'call', {
            start_date: startDate,
            end_date: endDate
        }).then(function (data) {
            renderCharts(data);
        });
    }

    return {
        applyDateFilter: applyDateFilter
    };
});
