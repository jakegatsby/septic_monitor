export default Vue.component('SettingsDialog', {
	template: `
            <v-card>
                <v-toolbar dark>
                    <v-btn icon @click="$emit('update:settingsOpen',false);">
                        <v-icon>mdi-close</v-icon>
                    </v-btn>
                    <v-toolbar-title>Settings</v-toolbar-title>
                    <v-spacer></v-spacer>
                    <v-toolbar-items>
                        <v-btn dark text @click="$emit('update:settingsOpen',false);">Save</v-btn>
                    </v-toolbar-items>
                </v-toolbar>
                SETTINGS: {{ settingsOpen }}
            </v-card>
	`,
	props: ["settingsOpen"],
	data: () => ({}),
});
