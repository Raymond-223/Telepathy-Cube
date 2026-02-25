var express = require('express');
var router = express.Router();

/* GET simulation page. */
router.get('/', function(req, res, next) {
  res.render('simulation', { title: 'Three.js 桌面仿真环境' });
});

module.exports = router;
