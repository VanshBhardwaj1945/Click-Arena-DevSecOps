/**
 * - Run `npm run dev` in your terminal to start a development server
 * - Run `curl "http://localhost:8787/__scheduled?cron=*+*+*+*+*"` to see your worker in action
 * - Run `npm run deploy` to publish your worker
 */

const PUBLIC_PATHS = ['/', '/health', '/favicon.ico'];
const VALID_API_KEYS = new Set(['sk_arena_dev_123', 'sk_arena_prod_456']);
const stats = { allowed: 0, blocked: 0, total: 0 };

async function forwardToAzure(azureUrl, req) {
	const azureResponse = await fetch(azureUrl, {
		method: req.method,
		headers: req.headers,
		body: req.method !== 'GET' ? req.body : null
	});

	const newResponse = new Response(azureResponse.body, azureResponse);

	newResponse.headers.set('X-Frame-Options', 'DENY');
	newResponse.headers.set('X-Content-Type-Options', 'nosniff');
	newResponse.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
	newResponse.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
	newResponse.headers.set('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline'");

	return newResponse;
}


export default {
	async fetch(req) {
		const url = new URL(req.url);
		const path = url.pathname;
		const azureUrl = 'https://click-arena.mangobush-de01fc2e.eastus.azurecontainerapps.io' + path;
		stats.total += 1;
		const isPublic = PUBLIC_PATHS.includes(path) || path.startsWith('/socket.io');

		if (isPublic) {
			return forwardToAzure(azureUrl, req);
			
		} 
		else {
			const apiKey = req.headers.get('X-API-Key')
			if (VALID_API_KEYS.has(apiKey)) {
				stats.allowed += 1;
        		return forwardToAzure(azureUrl, req);
			}
			else {
				stats.blocked += 1;
            	return new Response("Blocked - invalid API key", { status: 401 });

			}
		}
	},


	async scheduled(event, env, ctx) {

		console.log('[AUDIT] ' + new Date().toISOString() )
		console.log('[AUDIT] ALlowed: ' + stats.allowed)
		console.log('[AUDIT] Blocked: ' + stats.blocked)
		console.log('[AUDIT] Total Requests: ' + stats.total)

		let blockRate
		if (stats.total > 0) {
			 blockRate = ((stats.blocked/stats.total) * 100).toFixed(1)
		} else {
			 blockRate = 0
		}
		console.log('[AUDIT] Block Rate :  ' + blockRate)

	},

};
