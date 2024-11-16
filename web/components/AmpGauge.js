export default Vue.component('AmpGauge', {
    template: `
    <v-card shaped outlined height="100%">
        <v-card-title>Pump Amperage</v-card-title>
        <v-card-subtitle>
            <div>Last Reading: {{ amperage }} A</div>
            <div>Last Update: {{ lastUpdateStr }}</div>
            <div>Warning Level: {{ maxAmperage }}</div>
        </v-card-subtitle>
        <v-card-text>
            <canvas id="amp-gauge"></canvas>
        </v-card-text>
    </v-card>
    `,
    data: () => ({
        maxAmperage: 15,  // FIXME
        amperage: null,
        lastUpdate: null,
        chart: null,
        refresh_interval: 2000,        
        colorOk: "rgb(40, 167, 69)",
        colorWarn: "rgb(220, 53, 69)",
        colorBg: "rgb(248, 249, 250)",
    }),
    computed: {
        lastUpdateStr: function() {
            if (this.lastUpdate) {
                return this.lastUpdate.replace('T', ' @ ');
            } else {
                return "N/A";
            }
        }        
    },
    methods: {
        async getAmperage() {
            var r = await axios.get('/api/pump/amperage/');
            return r.data;
        },
        async update() {
            var a = await this.getAmperage();
            var amperage = a.value;
            this.chart.data.datasets[0].data = [amperage, this.maxAmperage - amperage];            
            this.chart.update();
            this.amperage = amperage;  // update chart before updating var
            this.lastUpdate = a.timestamp;
        }        
    },
    async mounted() {
        var a = await this.getAmperage();
        this.amperage = a.value;
        this.lastUpdate = a.timestamp;
        this.chart = new Chart(document.getElementById('amp-gauge'), {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [this.amperage, this.maxAmperage - this.amperage],
                    backgroundColor: [this.colorOk, this.colorBg]
                }],
            },
            options: {
                tooltips: {
                    enabled: false,
                }
            }
        });  // this.chart

        this.chart.options.animation.duration = 0;
        setInterval(this.update, this.refresh_interval);
    } // mounted
});
