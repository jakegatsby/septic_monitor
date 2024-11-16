export default Vue.component('AmpChart', {
    template: `
    <div>
        <canvas :id="chartId"></canvas>
    </div>
    `,
    props: ["duration"],
    data: () => ({
        amperages: [],
        chart: null,
        refresh_interval: 2000,
        maxAmperage: 15,  // FIXME
        colorLine: "rgb(54, 162, 235)",
		colorWarn: "rgb(220, 53, 69)",
    }),
    computed: {
        chartId: function() {
            return `amp-${this.duration}-chart`;
        }
    },
    methods: {
        async getAmperages() {
            const r = await axios.get(`/api/pump/amperage/${this.duration}/`);
            return r.data;
        },
        async update() {
            var amperages = await this.getAmperages();
            this.chart.data.datasets[0].data = amperages;
            this.chart.data.datasets[1].data = [{x: amperages[0].x, y: this.maxAmperage}, {x: amperages.at(-1).x, y: this.maxAmperage}],
            this.chart.update();
            this.amperages = amperages;
        }
    },
    async mounted() {
        this.amperages = await this.getAmperages();
        this.chart = new Chart(document.getElementById(this.chartId), {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: "Pump Amperage",
                        data: this.amperages,
                        borderColor: this.colorLine,
                        tension: 0.4,
                        fill: "start",
                    },
                    {
                        label: "Max Safe",
                        fill: "start",
                        data: [{x: this.amperages[0].x, y: this.maxAmperage}, {x: this.amperages.at(-1).x, y: this.maxAmperages}],
                        borderColor: this.colorWarn,
                    }

                ],
            },
            options: {
                scaleBeginAtZero: true,
                elements: {
                    point: {
                    	radius: 0
                    }	
                },
                scales: {
                    x: {
                        type: 'time',
                    }
                },
            }
        });  // this.chart

        this.chart.options.animation.duration = 0;
        setInterval(() => {this.update();},   this.refresh_interval);
    } // mounted
});


