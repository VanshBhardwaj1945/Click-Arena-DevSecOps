/**
 * - Run `npm run dev` in your terminal to start a development server
 * - Run `curl "http://localhost:8787/__scheduled?cron=*+*+*+*+*"` to see your worker in action
 * - Run `npm run deploy` to publish your worker
 */

const PUBLIC_PATHS = ['/', '/health', '/favicon.ico'];
const VALID_API_KEYS = new Set(['sk_arena_dev_123', 'sk_arena_prod_456']);
const stats = { allowed: 0, blocked: 0, total: 0 };

export default {
	async fetch(req) {
		const url = new URL(req.url);
		const path = url.pathname;

		stats.total += 1;

		if (PUBLIC_PATHS.includes(path)) {
			return new Response("Public path - Allowed")
		} 
		else {
			const apiKey = req.headers.get('X-API-Key')
			if (VALID_API_KEYS.has(apiKey)) {
				stats.allowed += 1;
				return new Response("Allowed")
			}
			else {
				stats.blocked += 1;
            	return new Response("Blocked - invalid API key", { status: 401 });

			}
		}
	},

	// The scheduled handler is invoked at the interval set in our wrangler.jsonc's
	// [[triggers]] configuration.
	async scheduled(event, env, ctx) {
		// A Cron Trigger can make requests to other endpoints on the Internet,
		// publish to a Queue, query a D1 Database, and much more.
		//
		// We'll keep it simple and make an API call to a Cloudflare API:
		let resp = await fetch('https://api.cloudflare.com/client/v4/ips');
		let wasSuccessful = resp.ok ? 'success' : 'fail';

		// You could store this result in KV, write to a D1 Database, or publish to a Queue.
		// In this template, we'll just log the result:
		console.log(`trigger fired at ${event.cron}: ${wasSuccessful}`);
	},
};
