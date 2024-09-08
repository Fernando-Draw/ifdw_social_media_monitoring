/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, useState } from "@odoo/owl";
import { Chart } from 'chart.js/auto';

class AnalyticsGraphSmmonitor extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            startDate: '',
            endDate: '',
        });
        onMounted(() => this.renderDashboard());
    }

    async renderDashboard() {
        const data = await this.fetchData();
        this.renderCharts(data);
    }

    async fetchData() {
        const [startDate, endDate] = [this.state.startDate, this.state.endDate];
        return this.orm.call('project.task.analyticsgraph.smmonitor', 'get_filtered_data', [], {
            start_date: startDate,
            end_date: endDate,
        });
    }

    renderCharts(data) {
        if (!data || !data.labels || !data.engagement || !data.interactions || !data.reach || !data.impressions) {
            console.error("Se recibieron datos no válidos para representar gráficos:", data);
            return;
        }

        const ctxBar = document.getElementById('barChart').getContext('2d');
        const ctxLine = document.getElementById('lineChart').getContext('2d');

        new Chart(ctxBar, {
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
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });

        new Chart(ctxLine, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [
                    { label: 'Engagement', borderColor: '#FF6384', data: data.engagement, fill: false, tension: 0.4 },
                    { label: 'Interactions', borderColor: '#36A2EB', data: data.interactions, fill: false, tension: 0.4 },
                    { label: 'Reach', borderColor: '#FFCE56', data: data.reach, fill: false, tension: 0.4 },
                    { label: 'Impressions', borderColor: '#4BC0C0', data: data.impressions, fill: false, tension: 0.4 }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    async applyDateFilter() {
        await this.renderDashboard();
    }
}
AnalyticsGraphSmmonitor.template = 'AnalyticsGraphSmmonitorTemplate';
registry.category("actions").add("analytics_graph_smmonitor", AnalyticsGraphSmmonitor);