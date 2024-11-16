import Status from './components/Status.js';
import LevelGauge from './components/LevelGauge.js';
import LevelChart from './components/LevelChart.js';
import AmpGauge from './components/AmpGauge.js';
import AmpChart from './components/AmpChart.js';
import SettingsDialog from './components/SettingsDialog.js';


Vue.use(Vuex);
Vue.use(Vuetify);


const store = new Vuex.Store({
    state: {
        maxLevel: null,
    },
    mutations: {
        setMaxLevel(state, level) {
            state.maxLevel = level;
        }
    }
})


new Vue({
    el: "#app",
    store: store,
    vuetify: new Vuetify(),
    template: `
        <v-app style="background-color: #eee">
          <v-main>
            <v-container fluid>

               <v-toolbar src="/background.jpg">
                  <v-toolbar-title class="ml-4">SepMon</v-toolbar-title>
                  <v-spacer></v-spacer>
                  <v-dialog v-model="settingsOpen" fullscreen hide-overlay>
                    <template v-slot:activator="{on, attrs}">
                      <v-btn icon v-bind="attrs" v-on="on">
                          <v-icon>mdi-dots-vertical</v-icon>
                      </v-btn>
                    </template>
                    <SettingsDialog :settings-open.sync="settingsOpen"></SettingsDialog>
                  </v-dialog>
                </v-toolbar>
                                
                <v-row align="top" justify="center" class="mt-8">
                    <v-col><Status></Status></v-col>
                    <v-col><LevelGauge></LevelGauge></v-col>
                    <v-col><AmpGauge></AmpGauge></v-col>
                </v-row>
                <v-row>
                  <iframe src="http://192.168.2.153:8080/d-solo/1zhwXOZRz/main-dashboard?orgId=1&panelId=2" width="450" height="200" frameborder="0"></iframe>                </v-row>
               	<v-row>    
                    <v-col>
                        <v-card shaped outlined height="100%">
                            <v-card-title>Pump Amperage</v-card-title>
                            <v-card-text>
                                <v-tabs v-model="ampTabs">                       
                                    <v-tab>Day</v-tab>
                                    <v-tab>Week</v-tab>
                                    <v-tab>Month</v-tab>
                                </v-tabs>
                                <v-tabs-items v-model="ampTabs">                                    
                                    <v-tab-item><AmpChart duration="day"></AmpChart></v-tab-item>
                                    <v-tab-item><AmpChart duration="week"></AmpChart></v-tab-item>
                                    <v-tab-item><AmpChart duration="month"></AmpChart></v-tab-item>                                
                                </v-tabs-items>
                            </v-card-text>
                        </v-card>
                    </v-col>
                </v-row>

            </v-container>
          </v-main>
        </v-app>
    `,
    components: {
        SettingsDialog,
        Status,
        LevelGauge,
        LevelChart,
        AmpGauge,
        AmpChart,
    },
    data() {
        return {
            settingsOpen: false,
            levelTabs: null,
            ampTabs: null,
        };
    },
});
