const express = require('express');
const _ = require('lodash');
const path = require('path');

const app = express();
const meldingen = [];

app.use(express.json());
app.use('/vendor', express.static(path.join(__dirname, 'public/vendor')));
app.get('/', (req, res) => res.sendFile(path.join(__dirname, 'views/index.html')));

app.post('/api/meldingen', (req, res) => {
  const melding = _.pick(req.body, ['paalnummer', 'omschrijving', 'email']);
  melding.id = meldingen.length + 1;
  meldingen.push(melding);
  res.status(201).json(melding);
});

app.get('/api/meldingen', (req, res) => res.json(_.sortBy(meldingen, 'id')));

app.listen(process.env.PORT || 3000);
