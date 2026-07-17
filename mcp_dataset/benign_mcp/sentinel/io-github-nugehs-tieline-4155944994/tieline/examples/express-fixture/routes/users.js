// Leaf router defined with express.Router() and a mix of param/non-param routes.
const express = require('express');

const router = express.Router();

router.get('/', (req, res) => res.json([]));
router.post('/', (req, res) => res.sendStatus(201));
router.get('/:id', (req, res) => res.json({ id: req.params.id }));
router.delete('/:id', (req, res) => res.sendStatus(204));

module.exports = router;
