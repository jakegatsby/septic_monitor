export default Vue.component('Status', {	
	template: `
    <v-card shaped outlined height="100%">
        <v-card-title>Status</v-card-title>
        <v-card-text>        	
            <v-alert v-for="msg in status.warn" :key="msg" type="error">{{ msg }}</v-alert>
            <v-alert v-for="msg in status.info" :key="msg" type="success">{{ msg }}</v-alert>
        </v-card-text>
    </v-card>
	`,
	data: () => ({
		refresh_interval: 2000,
		status: {},
	}),
	methods: {
	  async getStatus() {
	      try {
		      var r = await axios.get('/api/status/');
		      this.status =  r.data;
		  } catch {
		  	  this.status = {warn: ["Unable to contact REST backend!"]};
		  }
	  },
	},
	async mounted() {
		await this.getStatus();
		setInterval(() => {
				this.getStatus();
			},
			this.refresh_interval
		);
	} // mounted
});
