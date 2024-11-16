export default Vue.component('LevelGauge', {
    template: `
    <v-card shaped outlined height="100%">
        <v-card-title>Tank Level</v-card-title>
        <v-card-subtitle>
            <div>Last Reading: {{ absLevel }} cm from sensor</div>
            <div>Last Update: {{ lastUpdateStr }}</div>
            <div>Warning Level: {{ maxLevel }}</div>
        </v-card-subtitle>
        <v-card-text>
            <canvas id="level-gauge"></canvas>
        </v-card-text>
    </v-card>
    `,
    data: () => ({
        maxLevel: -5,  // FIXME
        level: null,
        lastUpdate: null,
        lowestLevel: -40,  // FIXME
        chart: null,
        refresh_interval: 2000,        
        colorOk: "rgb(54, 162, 235)",
        colorWarn: "rgb(220, 53, 69)",
    }),
    computed: {
        absLevel: function() {
            return Math.abs(this.level);
        },
        lastUpdateStr: function() {
            if (this.lastUpdate) {
                return this.lastUpdate.replace('T', ' @ ');
            } else {
                return "N/A";
            }
        }
    },
    methods: {
        async getLevel() {
            var r = await axios.get('/api/tank/level/');
            return r.data;  // wait to refresh gauge before set data attr
        },
        async update() {
            var l = await this.getLevel();
            var level = l.value;
            this.chart.data.datasets[0].data = [[this.lowestLevel, level]];            
            if (level > this.maxLevel) {
              this.chart.data.datasets[0].backgroundColor = this.colorWarn;
            } else {
              this.chart.data.datasets[0].backgroundColor = this.colorOk;
            }
            this.chart.update();
            this.level = level;
            this.lastUpdate = l.timestamp;
        }
    },
    async mounted() {
        var l = await this.getLevel();
        this.level = l.value;
        this.lastUpdate = l.timestamp;
        this.chart = new Chart(document.getElementById('level-gauge'), {
            type: 'bar',
            data: {
                labels: ["Level"],
                datasets: [{
                    data: [[this.lowestLevel, this.level]],
                    backgroundColor: this.colorOk,
                }],
            },
            options: {
                plugins: {
                    legend: {
                        display: false,
                    }
                },
                scales: {
                    y: {
                        ticks: {min: -40, max: 0}
                    }
                }
            }
        });  // this.chart

        this.chart.options.animation.duration = 0;
        setInterval(this.update, this.refresh_interval);
    } // mounted
});
