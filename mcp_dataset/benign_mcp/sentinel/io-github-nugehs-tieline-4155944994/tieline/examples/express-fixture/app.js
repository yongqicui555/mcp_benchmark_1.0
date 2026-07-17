// Entry point: defines the root app, mounts a sub-router under a prefix,
// and declares a couple of routes directly on the app.
const express = require('express');
const apiRouter = require('./routes/api');

const app = express();

app.use(express.json());
app.use('/api/v1', apiRouter);

app.get('/health', (req, res) => res.send('ok'));
app.route('/status')
  .get((req, res) => res.json({ up: true }))
  .post((req, res) => res.sendStatus(204));

module.exports = app;
