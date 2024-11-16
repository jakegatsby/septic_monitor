export default Vue.component('LevelChart', {
    template: `
    <div>
        <canvas :id="chartId"></canvas>
    </div>
    `,
    props: ["duration"],
    data: () => ({
        levels: [],
        chart: null,
        refresh_interval: 2000,
        maxLevel: -5,  // FIXME
        colorLine: "rgb(54, 162, 235)",
		colorWarn: "rgb(220, 53, 69)",
    }),
    computed: {
        chartId: function() {
            return `level-${this.duration}-chart`;
        }
    },
    methods: {
        async getLevels() {
            const r = await axios.get(`/api/tank/level/${this.duration}/`);
            return r.data;
        },
        async update() {
            var levels = await this.getLevels();
            this.chart.data.datasets[0].data = levels;
            this.chart.data.datasets[1].data = [{x: levels[0].x, y: this.maxLevel}, {x: levels.at(-1).x, y: this.maxLevel}],
            this.chart.data.datasets[2].data = [{x: levels[0].x, y: 0}, {x: levels.at(-1).x, y: 0}],
            this.chart.update();
            this.levels = levels;
        }
    },
    async mounted() {
        this.levels = await this.getLevels();
        this.chart = new Chart(document.getElementById(this.chartId), {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: "Water Level",
                        data: this.levels,
                        borderColor: this.colorLine,
                        tension: 0.1,
                        fill: "start",
                    },
                    {
                        label: "Max Safe",
                        fill: "start",
                        data: [{x: this.levels[0].x, y: this.maxLevel}, {x: this.levels.at(-1).x, y: this.maxLevel}],
                        borderColor: this.colorWarn,
                    },
                    {
                        label: "Sensor",
                        data: [{x: this.levels[0].x, y: 0}, {x: this.levels.at(-1).x, y: 0}],
                        borderColor: "dimgray",
                    }

                ],
            },
            options: {
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


