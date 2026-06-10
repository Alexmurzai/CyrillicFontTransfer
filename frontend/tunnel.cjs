const localtunnel = require('localtunnel');

(async () => {
  try {
    const tunnel = await localtunnel({ port: 8000 });
    console.log(`TUNNEL_URL=${tunnel.url}`);

    tunnel.on('close', () => {
      console.log('Tunnel closed');
    });

    tunnel.on('error', (err) => {
      console.log('Tunnel error:', err);
    });
  } catch (err) {
    console.log('Error creating tunnel:', err);
  }
})();
