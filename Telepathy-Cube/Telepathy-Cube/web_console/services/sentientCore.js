'use strict';

const fs = require('fs');
const path = require('path');

const MODE = {
  AMBIENT: 'ambient',
  FOCUS: 'focus'
};

const EMOTION_CONFIG = {
  calm: { duration: 4.0, minAngle: 30, maxAngle: 60, color: '#4ECDC4' },
  anxious: { duration: 2.0, minAngle: 40, maxAngle: 80, color: '#FF6B6B' },
  relaxed: { duration: 6.0, minAngle: 20, maxAngle: 50, color: '#96CEB4' },
  excited: { duration: 1.5, minAngle: 50, maxAngle: 90, color: '#FFD166' },
  deepSleep: { duration: 8.0, minAngle: 10, maxAngle: 40, color: '#7B68EE' },
  meditative: { duration: 10.0, minAngle: 15, maxAngle: 45, color: '#9370DB' }
};

function parseIntent(text) {
  const query = String(text || '').trim();
  if (!query) {
    return { type: 'chat', content: '' };
  }

  if (query.includes('在哪') || query.includes('哪里')) {
    const item = query
      .replace(/[？?]/g, '')
      .replace('我的', '')
      .replace('在哪', '')
      .replace('哪里', '')
      .trim();
    return { type: 'find', item };
  }

  if (query.includes('提醒')) {
    const parts = query.split('提醒');
    const timeText = (parts[0] || '').trim();
    const content = (parts.slice(1).join('提醒') || '').trim();
    return { type: 'reminder', timeText, content };
  }

  if (query.includes('左脑') || query.includes('右脑') || query.includes('模式')) {
    return {
      type: 'mode',
      value: query.includes('左脑') ? MODE.FOCUS : MODE.AMBIENT
    };
  }

  return { type: 'chat', content: query };
}

function ensureStoreFile(storePath) {
  if (fs.existsSync(storePath)) {
    return;
  }
  const initData = {
    objects: [],
    reminders: []
  };
  fs.mkdirSync(path.dirname(storePath), { recursive: true });
  fs.writeFileSync(storePath, JSON.stringify(initData, null, 2), 'utf8');
}

function parseReminderTime(timeText) {
  const now = new Date();
  const target = new Date(now);

  const raw = String(timeText || '');
  if (raw.includes('后天')) {
    target.setDate(target.getDate() + 2);
  } else if (raw.includes('明天')) {
    target.setDate(target.getDate() + 1);
  }

  const hourMatch = raw.match(/(\d{1,2})\s*点/);
  const minuteMatch = raw.match(/(\d{1,2})\s*分/);
  const hour = hourMatch ? Number(hourMatch[1]) : 9;
  const minute = minuteMatch ? Number(minuteMatch[1]) : 0;
  target.setHours(hour, minute, 0, 0);

  if (target <= now) {
    target.setDate(target.getDate() + 1);
  }

  return target.toISOString();
}

class SentientCore {
  constructor(options = {}) {
    this.mode = MODE.AMBIENT;
    this.emotion = 'calm';
    this.lastResponse = '';
    this.status = {
      breath: '运行中',
      gimbal: '收起',
      laser: '关闭'
    };
    this.storePath = options.storePath || path.join(__dirname, '..', 'data', 'memory.json');
    ensureStoreFile(this.storePath);
  }

  getStore() {
    return JSON.parse(fs.readFileSync(this.storePath, 'utf8'));
  }

  saveStore(store) {
    fs.writeFileSync(this.storePath, JSON.stringify(store, null, 2), 'utf8');
  }

  setMode(mode) {
    if (mode !== MODE.AMBIENT && mode !== MODE.FOCUS) {
      throw new Error(`invalid mode: ${mode}`);
    }
    this.mode = mode;
    if (mode === MODE.AMBIENT) {
      this.status = { breath: '运行中', gimbal: '收起', laser: '关闭' };
    } else {
      this.status = { breath: '暂停', gimbal: '升起', laser: '关闭' };
    }
    return this.getStatus();
  }

  setEmotion(emotion) {
    if (!EMOTION_CONFIG[emotion]) {
      throw new Error(`invalid emotion: ${emotion}`);
    }
    this.emotion = emotion;
    return this.getStatus();
  }

  rememberObject(name, location, confidence = 0.9) {
    const store = this.getStore();
    store.objects.push({
      id: `obj_${Date.now()}`,
      name,
      location,
      confidence,
      timestamp: new Date().toISOString()
    });
    this.saveStore(store);
  }

  findObject(name) {
    const store = this.getStore();
    const history = store.objects
      .filter(item => item.name === name)
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

    const latest = history[0];
    this.setMode(MODE.FOCUS);
    if (!latest) {
      this.lastResponse = `没有找到${name}的位置信息。`;
      return {
        found: false,
        message: this.lastResponse
      };
    }

    this.status.gimbal = '锁定目标';
    this.status.laser = '照射中';
    this.lastResponse = `${name}在${latest.location}。`;
    return {
      found: true,
      message: this.lastResponse,
      location: latest.location,
      confidence: latest.confidence,
      timestamp: latest.timestamp
    };
  }

  addReminder(timeText, content) {
    const store = this.getStore();
    const remindAt = parseReminderTime(timeText);
    const reminder = {
      id: `rem_${Date.now()}`,
      content,
      timeText,
      remindAt,
      status: 'pending',
      createdAt: new Date().toISOString()
    };
    store.reminders.push(reminder);
    this.saveStore(store);
    return reminder;
  }

  getReminders() {
    return this.getStore().reminders.slice().sort((a, b) => new Date(a.remindAt) - new Date(b.remindAt));
  }

  processCommand(text) {
    const intent = parseIntent(text);
    if (intent.type === 'find') {
      return { intent, result: this.findObject(intent.item) };
    }
    if (intent.type === 'reminder') {
      const reminder = this.addReminder(intent.timeText, intent.content || '事项');
      this.lastResponse = `已设置提醒：${intent.timeText} 提醒 ${intent.content || '事项'}`;
      return { intent, result: reminder, message: this.lastResponse };
    }
    if (intent.type === 'mode') {
      this.setMode(intent.value);
      this.lastResponse = intent.value === MODE.FOCUS ? '已切换到左脑模式' : '已切换到右脑模式';
      return { intent, mode: this.mode, message: this.lastResponse };
    }
    this.lastResponse = '我在，已收到你的指令。';
    return { intent, message: this.lastResponse };
  }

  clearLaser() {
    this.status.laser = '关闭';
    if (this.mode === MODE.FOCUS) {
      this.status.gimbal = '待命';
    }
  }

  getStatus() {
    return {
      mode: this.mode,
      emotion: this.emotion,
      emotionConfig: EMOTION_CONFIG[this.emotion],
      status: this.status,
      lastResponse: this.lastResponse
    };
  }
}

module.exports = {
  SentientCore,
  MODE,
  EMOTION_CONFIG,
  parseIntent
};

