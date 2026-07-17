// A mid-tier router: has its own route AND nests another router under a prefix.
// Exercises transitive prefix composition: app(/api/v1) -> api(/users) -> users.
const { Router } = require('express');
const usersRouter = require('./users');

const router = Router();

router.use('/users', usersRouter);
router.get('/ping', (req, res) => res.send('pong'));

module.exports = router;
