# Deploying to Fly.io

Use the following commands to deploy the application:

```
fly auth signup # or: fly auth login
fly launch --internal-port 8080
fly secrets set LASTFM_API_KEY=... SPOTIFY_CLIENT_ID=... SPOTIFY_CLIENT_SECRET=... SECRET_KEY=...
fly deploy
fly status
fly logs
fly apps open
```
