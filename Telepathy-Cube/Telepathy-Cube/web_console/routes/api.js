'use strict';

const express = require('express');
const path = require('path');
const { SentientCore, MODE } = require('../services/sentientCore');

const router = express.Router();
const core = new SentientCore({
  storePath: path.join(__dirname, '..', 'data', 'memory.json')
});

router.get('/status', (req, res) => {
  res.json(core.getStatus());
});

router.post('/mode', (req, res) => {
  try {
    const mode = req.body?.mode;
    if (mode !== MODE.AMBIENT && mode !== MODE.FOCUS) {
      return res.status(400).json({ error: 'invalid mode' });
    }
    const status = core.setMode(mode);
    return res.json(status);
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
});

router.post('/emotion', (req, res) => {
  try {
    const emotion = req.body?.emotion;
    const status = core.setEmotion(emotion);
    return res.json(status);
  } catch (error) {
    return res.status(400).json({ error: error.message });
  }
});

router.post('/memory/objects', (req, res) => {
  const name = String(req.body?.name || '').trim();
  const location = String(req.body?.location || '').trim();
  const confidence = Number(req.body?.confidence || 0.9);
  if (!name || !location) {
    return res.status(400).json({ error: 'name and location are required' });
  }
  core.rememberObject(name, location, confidence);
  return res.status(201).json({ ok: true });
});

router.post('/find', (req, res) => {
  const name = String(req.body?.name || '').trim();
  if (!name) {
    return res.status(400).json({ error: 'name is required' });
  }
  const result = core.findObject(name);
  if (result.found) {
    setTimeout(() => core.clearLaser(), 5000);
  }
  return res.json({ ...core.getStatus(), result });
});

router.get('/reminders', (req, res) => {
  return res.json({ reminders: core.getReminders() });
});

router.post('/reminders', (req, res) => {
  const timeText = String(req.body?.timeText || '').trim();
  const content = String(req.body?.content || '').trim();
  if (!timeText || !content) {
    return res.status(400).json({ error: 'timeText and content are required' });
  }
  const reminder = core.addReminder(timeText, content);
  return res.status(201).json({ reminder });
});

router.post('/command', (req, res) => {
  const text = String(req.body?.text || '').trim();
  if (!text) {
    return res.status(400).json({ error: 'text is required' });
  }
  const result = core.processCommand(text);
  return res.json({ ...core.getStatus(), result });
});

module.exports = router;

