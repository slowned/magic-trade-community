const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
	devServer: {
		host: '0.0.0.0', // Allow connections from outside the container
		port: 3000,      // Use port 3000 for development
	},
})
