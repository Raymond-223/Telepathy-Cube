/**
 * 灵犀魔方 (Sentient Cube) - Web仿真主模块 v4.0
 * 增强版：复杂桌面环境 + 真实遮挡模拟 + 射线检测激光 + 完善的情绪系统
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';

// ==================== 生物呼吸波形生成器 ====================
class BiologicalWaveGenerator {
    static getWave(phaseProgress) {
        // 基于suib.py的生物呼吸波形: exp(sin(phase)) + 谐波
        const phase = phaseProgress * 2 * Math.PI;
        const wave1 = Math.exp(Math.sin(phase)) - (1 / Math.E);
        const wave2 = 0.3 * Math.sin(phase * 2);
        const wave3 = 0.1 * Math.sin(phase * 3 + 0.5);
        const rawValue = wave1 + wave2 + wave3;
        const normalized = rawValue / (Math.E - (1 / Math.E) + 0.3 + 0.1);
        return Math.max(0, Math.min(1, normalized));
    }
}

// ==================== 情绪参数配置 (Updated) ====================
const EMOTION_CONFIG = {
    calm: {
        duration: 4.0, minAngle: 30, maxAngle: 60,
        color: 0x4ECDC4, name: '平静', emoji: '😌'
    },
    anxious: {
        duration: 2.0, minAngle: 40, maxAngle: 80,
        color: 0xFF6B6B, name: '焦虑', emoji: '😰'
    },
    relaxed: {
        duration: 6.0, minAngle: 20, maxAngle: 50,
        color: 0x96CEB4, name: '放松', emoji: '😊'
    },
    excited: {
        duration: 1.5, minAngle: 50, maxAngle: 90,
        color: 0xFFD166, name: '兴奋', emoji: '🤩'
    },
    deepSleep: {
        duration: 8.0, minAngle: 10, maxAngle: 40,
        color: 0x7B68EE, name: '深睡', emoji: '😴'
    },
    meditative: {
        duration: 10.0, minAngle: 15, maxAngle: 45,
        color: 0x9370DB, name: '冥想', emoji: '🧘'
    }
};

// ==================== 幻影点阵屏模块 ====================
class PhantomLED {
    constructor(cols = 16, rows = 8) {
        this.cols = cols;
        this.rows = rows;
        this.pixels = [];
        this.group = new THREE.Group();
        this.currentColor = 0xffaa44;
        this.displayText = '';
        this.scrollOffset = 0;
        this.isScrolling = false;

        // 表情库 (复用之前的模式，颜色动态调整)
        this.emotions = {
            happy: this.createPattern('happy'),
            sleep: this.createPattern('sleep'),
            focus: this.createPattern('focus'),
            locate: this.createPattern('locate'),
            found: this.createPattern('found')
        };

        this.currentEmotion = 'sleep';
        this.init();
    }

    createPattern(type) {
        // 简化的16x8图案定义
        const patterns = {
            happy: [
                [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
                [0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1],
                [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0],
                [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            ],
            sleep: [
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            ],
            focus: [
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
                [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            ],
            locate: [
                [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0]
            ],
            found: [
                [0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
                [1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0],
                [1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 0],
                [0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
            ]
        };
        return patterns[type] || patterns.sleep;
    }

    init() {
        const pixelSize = 0.005; // 缩小像素点
        const gap = 0.001;       // 缩小间距
        const totalWidth = (pixelSize + gap) * this.cols;
        const totalHeight = (pixelSize + gap) * this.rows;

        // 背板 - 改为深色不透明，模拟OLED黑底
        const backGeom = new THREE.PlaneGeometry(totalWidth + 0.01, totalHeight + 0.01);
        const backMat = new THREE.MeshBasicMaterial({ color: 0x0a0a12, transparent: true, opacity: 0.95 });
        const back = new THREE.Mesh(backGeom, backMat);
        // Backplate at local 0 (will be at world 0.061)
        back.position.z = 0;
        this.group.add(back);

        // 创建像素
        for (let y = 0; y < this.rows; y++) {
            this.pixels[y] = [];
            for (let x = 0; x < this.cols; x++) {
                // 增大填充率: 半径设为 pixelSize * 0.48 (几乎填满格子)
                const geom = new THREE.CircleGeometry(pixelSize * 0.48, 8);
                const mat = new THREE.MeshBasicMaterial({ color: 0x111118, transparent: true, opacity: 0.1 }); // 熄灭时低亮度
                const pixel = new THREE.Mesh(geom, mat);
                pixel.position.set(
                    x * (pixelSize + gap) - totalWidth / 2 + pixelSize / 2,
                    -y * (pixelSize + gap) + totalHeight / 2 - pixelSize / 2,
                    0.001 // Pixels slightly in front of backplate
                );
                this.pixels[y][x] = pixel;
                this.group.add(pixel);
            }
        }
    }

    setEmotion(emotionName, color) {
        this.currentEmotion = emotionName;
        this.currentColor = color;
        this.isScrolling = false;
        // 如果是6种基本情绪模式，统一用sleep/focus等图案，还是每个情绪有独特图案？
        // 这里简化：所有情绪默认用sleep图案（作为背景），颜色不同
        // 特殊状态用特殊图案
        let patternKey = 'sleep';
        if (emotionName === 'focus') patternKey = 'focus';
        else if (emotionName === 'locate') patternKey = 'locate';

        const pattern = this.emotions[patternKey];
        if (!pattern) return;

        for (let y = 0; y < this.rows; y++) {
            for (let x = 0; x < this.cols; x++) {
                const isOn = pattern[y] && pattern[y][x] === 1;
                this.pixels[y][x].material.color.setHex(isOn ? color : 0x111118);
                this.pixels[y][x].material.opacity = isOn ? 1.0 : 0.2;
            }
        }
    }

    showSuccess(color) {
        this.isScrolling = true;
        this.currentColor = color;
        this.renderSuccessAnim();
    }

    renderSuccessAnim() {
        // 简单的闪烁成功动画
        const pattern = this.emotions.found;
        const time = Date.now() / 200;

        for (let y = 0; y < this.rows; y++) {
            for (let x = 0; x < this.cols; x++) {
                const isOn = pattern[y] && pattern[y][x] === 1;
                if (isOn) {
                    const flicker = Math.sin(time + x * 0.5) > 0 ? 1.0 : 0.3;
                    this.pixels[y][x].material.color.setHex(this.currentColor);
                    this.pixels[y][x].material.opacity = flicker;
                } else {
                    this.pixels[y][x].material.opacity = 0.1;
                }
            }
        }
    }

    update(time) {
        if (this.isScrolling) {
            this.renderSuccessAnim();
        } else {
            // 呼吸效果
            const patternKey = this.currentEmotion === 'focus' ? 'focus' :
                this.currentEmotion === 'locate' ? 'locate' : 'sleep';
            const pattern = this.emotions[patternKey];
            if (!pattern) return;

            for (let y = 0; y < this.rows; y++) {
                for (let x = 0; x < this.cols; x++) {
                    if (pattern[y] && pattern[y][x] === 1) {
                        const wave = 0.7 + 0.3 * Math.sin(time * 3 + x * 0.2 + y * 0.3);
                        this.pixels[y][x].material.opacity = wave;
                    }
                }
            }
        }
    }

    getMesh() { return this.group; }
}

// ==================== 仿生机械云台 (射线检测增强版) ====================
class BionicGimbal {
    constructor(scene, deskItems) {
        this.scene = scene;
        this.deskItems = deskItems; // 引用DeskItems以访问碰撞体
        this.group = new THREE.Group();
        this.periscopeGroup = new THREE.Group();
        this.headGroup = new THREE.Group();
        this.isRaised = false;
        this.currentHeight = -0.1;
        this.targetHeight = -0.1;
        this.panAngle = 0;
        this.tiltAngle = 0;
        this.targetPan = 0;
        this.targetTilt = 0;
        this.laserOn = false;
        this.targetMesh = null; // 目标物品mesh
        this.targetBlocked = false; // 目标是否被遮挡

        this.raycaster = new THREE.Raycaster();

        this.init();
    }

    init() {
        // ... (保持原有的几何体构建代码不变) ...
        // 底座
        const base = new THREE.Mesh(
            new THREE.CylinderGeometry(0.022, 0.026, 0.012, 16),
            new THREE.MeshStandardMaterial({ color: 0x2a2a2a, roughness: 0.3, metalness: 0.8 })
        );
        this.group.add(base);

        // 伸缩杆
        const pole = new THREE.Mesh(
            new THREE.CylinderGeometry(0.005, 0.005, 0.1, 8),
            new THREE.MeshStandardMaterial({ color: 0x444444, metalness: 0.7 })
        );
        pole.position.y = 0.05;
        this.periscopeGroup.add(pole);

        // 旋转平台
        const platform = new THREE.Mesh(
            new THREE.CylinderGeometry(0.015, 0.015, 0.008, 16),
            new THREE.MeshStandardMaterial({ color: 0x333333, metalness: 0.8 })
        );
        platform.position.y = 0.105;
        this.periscopeGroup.add(platform);

        // 摄像头头部
        const head = new THREE.Mesh(
            new THREE.SphereGeometry(0.014, 16, 16),
            new THREE.MeshStandardMaterial({ color: 0x1a1a1a, metalness: 0.9 })
        );
        this.headGroup.add(head);

        // 镜头
        const lens = new THREE.Mesh(
            new THREE.CylinderGeometry(0.006, 0.008, 0.01, 16),
            new THREE.MeshStandardMaterial({ color: 0x0066ff, emissive: 0x003388, emissiveIntensity: 0.8 })
        );
        lens.rotation.x = Math.PI / 2;
        lens.position.z = 0.015;
        this.headGroup.add(lens);

        // 激光发射器
        const laserEmitter = new THREE.Mesh(
            new THREE.CylinderGeometry(0.002, 0.002, 0.006, 8),
            new THREE.MeshStandardMaterial({ color: 0xff0000, emissive: 0xff0000, emissiveIntensity: 0.5 })
        );
        laserEmitter.rotation.x = Math.PI / 2;
        laserEmitter.position.set(0, -0.008, 0.016);
        this.headGroup.add(laserEmitter);

        this.headGroup.position.y = 0.12;
        this.periscopeGroup.add(this.headGroup);

        // 激光光点
        const dot = new THREE.Mesh(
            new THREE.SphereGeometry(0.008, 8, 8),
            new THREE.MeshBasicMaterial({ color: 0xff0000, transparent: true, opacity: 0.9 })
        );
        this.laserDot = dot;
        this.laserDot.visible = false;

        // 激光光晕
        const halo = new THREE.Mesh(
            new THREE.RingGeometry(0.01, 0.02, 16),
            new THREE.MeshBasicMaterial({ color: 0xff0000, transparent: true, opacity: 0.4, side: THREE.DoubleSide })
        );
        this.laserHalo = halo;
        this.laserHalo.visible = false;

        // 激光束线 (新增)
        const beamGeo = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 0, -1)]);
        this.laserBeam = new THREE.Line(beamGeo, new THREE.LineBasicMaterial({ color: 0xff0000, transparent: true, opacity: 0.3 }));
        this.laserBeam.visible = false;
        this.scene.add(this.laserBeam);

        this.periscopeGroup.position.y = -0.1;
        this.periscopeGroup.visible = false;
        this.group.add(this.periscopeGroup);
    }

    raise() {
        this.isRaised = true;
        this.targetHeight = 0.015;
        this.periscopeGroup.visible = true;
    }

    lower() {
        this.isRaised = false;
        this.targetHeight = -0.1;
        this.setLaser(false);
    }

    pointToPosition(targetWorldPos, cubeWorldPos) {
        // 计算目标角度
        const dx = targetWorldPos.x - cubeWorldPos.x;
        const dy = targetWorldPos.y - (cubeWorldPos.y + 0.19);
        const dz = targetWorldPos.z - cubeWorldPos.z;
        this.targetPan = Math.atan2(dx, dz);
        const hDist = Math.sqrt(dx * dx + dz * dz);
        this.targetTilt = -Math.atan2(dy, hDist);
    }

    setLaser(on) {
        this.laserOn = on;
        this.laserDot.visible = on;
        this.laserHalo.visible = on;
        this.laserBeam.visible = on;
    }

    update(deltaTime, cubeWorldPos) {
        // 平滑升降
        this.currentHeight += (this.targetHeight - this.currentHeight) * 0.05;
        this.periscopeGroup.position.y = this.currentHeight;

        if (!this.isRaised && this.currentHeight <= -0.09) {
            this.periscopeGroup.visible = false;
        }

        // 平滑旋转
        this.panAngle += (this.targetPan - this.panAngle) * 0.05;
        this.tiltAngle += (this.targetTilt - this.tiltAngle) * 0.05;
        this.tiltAngle = Math.max(-0.8, Math.min(0.3, this.tiltAngle)); // 限制俯仰角

        this.periscopeGroup.rotation.y = this.panAngle;
        this.headGroup.rotation.x = this.tiltAngle;

        // 激光射线检测逻辑
        if (this.laserOn && this.isRaised) {
            // 更新世界矩阵
            this.periscopeGroup.updateMatrixWorld(true);

            // 计算射线发射点 (激光发射器世界坐标)
            const emitterPos = new THREE.Vector3(0, -0.008, 0.016);
            this.headGroup.localToWorld(emitterPos);

            // 计算射线方向 - 使用正确的API
            const direction = new THREE.Vector3(0, 0, 1);
            const worldQuat = new THREE.Quaternion();
            this.headGroup.getWorldQuaternion(worldQuat);
            direction.applyQuaternion(worldQuat);
            direction.normalize();

            this.raycaster.set(emitterPos, direction);

            // 获取所有可碰撞物 (desk + items)
            const colliders = this.deskItems.getColliders();
            // 还需要加入地板/桌面本身，防止穿透到无限远
            // 简单起见，这里假设桌面是y=0.42的平面

            const intersects = this.raycaster.intersectObjects(colliders, true);

            let hitPoint = null;
            let hitTarget = false; // 是否打到目标物品
            if (intersects.length > 0) {
                hitPoint = intersects[0].point;
                // 检查打到的是否是目标物品
                if (this.targetMesh) {
                    let hitObj = intersects[0].object;
                    // 遍历父级检查是否是目标
                    while (hitObj) {
                        if (hitObj === this.targetMesh) {
                            hitTarget = true;
                            break;
                        }
                        hitObj = hitObj.parent;
                    }
                }
                // 防止光点穿模，稍微往回拉一点
                hitPoint.addScaledVector(direction, -0.005);
            } else {
                // 如果没打中物体，计算与桌面平面的交点 (y=0.42)
                const deskY = 0.42;
                if (direction.y < -0.01) {
                    const t = (deskY - emitterPos.y) / direction.y;
                    if (t > 0) {
                        hitPoint = emitterPos.clone().addScaledVector(direction, t);
                    }
                }
            }

            // 如果目标被遮挡，标记状态但不隐藏激光 (修正用户反馈"看不到激光")
            this.targetBlocked = (this.targetMesh && !hitTarget);
            const showLaser = !!hitPoint; // 只要打到物体就显示

            this.laserDot.visible = showLaser;
            this.laserHalo.visible = showLaser;
            this.laserBeam.visible = showLaser;

            if (showLaser && hitPoint) {
                this.laserDot.position.copy(hitPoint);
                this.laserHalo.position.copy(hitPoint);
                this.laserHalo.lookAt(emitterPos); // 光晕朝向光源

                // 更新光束
                const positions = this.laserBeam.geometry.attributes.position.array;
                positions[0] = emitterPos.x; positions[1] = emitterPos.y; positions[2] = emitterPos.z;
                positions[3] = hitPoint.x; positions[4] = hitPoint.y; positions[5] = hitPoint.z;
                this.laserBeam.geometry.attributes.position.needsUpdate = true;

                // 动画效果
                const flicker = 0.8 + 0.2 * Math.sin(Date.now() * 0.02);
                this.laserDot.material.opacity = flicker;
                this.laserHalo.material.opacity = flicker * 0.4;
                this.laserBeam.material.opacity = flicker * 0.3;
            }
        } else {
            // 激光关闭时也隐藏
            this.laserDot.visible = false;
            this.laserHalo.visible = false;
            this.laserBeam.visible = false;
        }
    }

    getSceneObjects() { return [this.laserDot, this.laserHalo]; }
    getMesh() { return this.group; }
}

// ==================== 呼吸律动系统 (保持不变) ====================
// (为了篇幅，直接复用之前的逻辑，只微调参数或颜色接口)
class BreathingSystem {
    // ... (代码与上一版相同，省略重复部分以节省空间，此处为完整逻辑的占位)
    constructor() {
        this.panels = [];
        this.isBreathing = true;
        this.group = new THREE.Group();
        this.cycleDuration = 4.0;
        this.minAngle = 30;
        this.maxAngle = 60;
        this.targetDuration = 4.0;
        this.targetMin = 30;
        this.targetMax = 60;
        this.accumulatedPhase = 0;
        this.lastTime = 0;
        this.transitionSpeed = 0.03;
        this.currentColorRGB = { r: 1, g: 0.67, b: 0.27 };
        this.targetColor = { r: 1, g: 0.67, b: 0.27 };
        this.init();
    }

    init() {
        const positions = [
            { x: 0.078, z: 0, ry: Math.PI / 2, axis: 'x' },
            { x: -0.078, z: 0, ry: -Math.PI / 2, axis: 'x' },
            { x: 0, z: 0.078, ry: 0, axis: 'z' },
            { x: 0, z: -0.078, ry: Math.PI, axis: 'z' }
        ];
        positions.forEach((pos, i) => {
            const panelGroup = new THREE.Group();
            const panel = new THREE.Mesh(
                new THREE.BoxGeometry(0.13, 0.13, 0.01),
                new THREE.MeshStandardMaterial({ color: 0x9b8b7a, roughness: 0.85, transparent: true, opacity: 0.98 })
            );
            panel.castShadow = true;
            panelGroup.add(panel);
            const edgeMat = new THREE.MeshBasicMaterial({ color: 0xffaa44, transparent: true, opacity: 0.5 });
            const topEdge = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.004, 0.012), edgeMat.clone());
            topEdge.position.y = 0.063;
            panelGroup.add(topEdge);
            const bottomEdge = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.004, 0.012), edgeMat.clone());
            bottomEdge.position.y = -0.063;
            panelGroup.add(bottomEdge);
            panelGroup.position.set(pos.x, 0, pos.z);
            panelGroup.rotation.y = pos.ry;
            this.panels.push({
                group: panelGroup,
                edges: [topEdge, bottomEdge],
                basePos: { x: pos.x, z: pos.z },
                axis: pos.axis,
                phaseOffset: i * Math.PI / 2
            });
            this.group.add(panelGroup);
        });
    }

    setEmotion(emotionKey) {
        const config = EMOTION_CONFIG[emotionKey];
        if (!config) return;
        this.targetDuration = config.duration;
        this.targetMin = config.minAngle;
        this.targetMax = config.maxAngle;
        const c = new THREE.Color(config.color);
        this.targetColor = { r: c.r, g: c.g, b: c.b };
    }

    update(time) {
        if (!this.isBreathing) return;
        const dt = time - this.lastTime;
        this.lastTime = time;

        this.cycleDuration += (this.targetDuration - this.cycleDuration) * this.transitionSpeed;
        this.minAngle += (this.targetMin - this.minAngle) * this.transitionSpeed;
        this.maxAngle += (this.targetMax - this.maxAngle) * this.transitionSpeed;
        this.currentColorRGB.r += (this.targetColor.r - this.currentColorRGB.r) * this.transitionSpeed;
        this.currentColorRGB.g += (this.targetColor.g - this.currentColorRGB.g) * this.transitionSpeed;
        this.currentColorRGB.b += (this.targetColor.b - this.currentColorRGB.b) * this.transitionSpeed;

        if (dt > 0 && dt < 0.1) this.accumulatedPhase += dt / this.cycleDuration;
        const phase = this.accumulatedPhase % 1.0;
        const wave = BiologicalWaveGenerator.getWave(phase);
        const angleRange = this.maxAngle - this.minAngle;
        const breathOffset = (angleRange / 180) * 0.08 * wave;

        this.panels.forEach((p, i) => {
            const localPhase = (this.accumulatedPhase + p.phaseOffset / (2 * Math.PI) * 0.3) % 1.0;
            const localWave = BiologicalWaveGenerator.getWave(localPhase);
            const offset = (angleRange / 180) * 0.06 * localWave;
            const dir = new THREE.Vector3(p.basePos.x, 0, p.basePos.z).normalize();
            p.group.position.x = p.basePos.x + dir.x * offset;
            p.group.position.z = p.basePos.z + dir.z * offset;

            const tilt = offset * 2.5;
            if (p.axis === 'x') p.group.rotation.z = tilt * (p.basePos.x > 0 ? 1 : -1);
            else p.group.rotation.x = tilt * (p.basePos.z > 0 ? -1 : 1);

            const c = new THREE.Color(this.currentColorRGB.r, this.currentColorRGB.g, this.currentColorRGB.b);
            const glowIntensity = 0.3 + 0.4 * localWave;
            p.edges.forEach(edge => {
                edge.material.color.copy(c);
                edge.material.opacity = glowIntensity;
            });
        });
    }

    setBreathing(enabled) { this.isBreathing = enabled; }
    getMesh() { return this.group; }
}

// ==================== 桌面物品管理 (大幅增强版) ====================
class DeskItems {
    constructor() {
        this.items = []; // 目标物品
        this.obstacles = []; // 障碍物
        this.group = new THREE.Group();
    }

    // 生成复杂桌面环境 (精确坐标，无穿模)
    generateClutteredDesk() {
        this.clear();
        // 桌面尺寸: 2.0 x 1.4, 中心在(0, 0.42, 0)
        // 魔方在(0, 0.51, 0)，占据中心约0.15x0.15区域

        // 1. 添加大件遮挡物 (分散在桌面四周)
        this.createBookStack(-0.75, 0.45);    // 左后方
        this.createBookStack(0.75, -0.45);    // 右前方
        this.createMug(-0.6, -0.5);           // 左前方
        // this.createPhotoFrame(-0.55, 0, 0.0); // [已移除]
        this.createDeskLamp(0.85, 0.55);      // 右后角
        this.createTissueBox(0.7, 0.25);      // 右侧中后
        this.createPlant(0.8, -0.2);          // 右前方 (新增)

        // 2. 添加目标物品 (已移除笔记本和钥匙)
        // this.createKeys(-0.3, 0.5);        // [已移除]
        this.createPhone(0.4, -0.35);         // 前方偏右
        this.createWallet(-0.8, 0.15);        // 左边缘
        // this.createGlasses(0.25, 0.45);       // [已移除]
        // this.createWatch(-0.45, -0.4);        // [已移除]

        // 剪刀移到更显眼的位置 (已移除)
        // this.createScissors(-0.2, 0.5);       // [已移除]

        this.createEarphones(0.55, 0.5);      // 右后方
        this.createCharger(-0.35, -0.55);     // 前方左侧
        this.createRemote(0.15, -0.5);        // 前方中间
        this.createPillBottle(-0.85, -0.25);  // 左边缘中部
        this.createUSBDrive(0.35, 0.15);      // 中右
        this.createLipstick(-0.15, 0.35);     // 中后偏左
    }

    addObstacles() {
        // 📚 书籍堆 (Stacks of Books)
        this.createBookStack(-0.35, 0.3);
        this.createBookStack(0.3, -0.35);

        // ☕ 马克杯 (Mug)
        this.createMug(0.35, -0.15);

        // 💡 台灯 (Desk Lamp)
        this.createDeskLamp(-0.4, -0.3);

        // 🧻 抽纸盒 (Tissue Box)
        this.createTissueBox(-0.2, -0.4);

        // 🪴 盆栽 (Plant)
        this.createPlant(0.5, 0.2);

        // 🖼️ 相框
        // this.createPhotoFrame(0.0, 0.5, 0); // [已移除]

        // 📄 散乱纸张
        for (let i = 0; i < 5; i++) {
            this.createPaper(
                (Math.random() - 0.5) * 0.8,
                (Math.random() - 0.5) * 0.8
            );
        }
    }

    createBookStack(x, z) {
        const colors = [0x8b4513, 0x228b22, 0x4682b4, 0xcd853f];
        const numBooks = 3 + Math.floor(Math.random() * 3);
        let currentY = 0;

        for (let i = 0; i < numBooks; i++) {
            const w = 0.15 + Math.random() * 0.05;
            const h = 0.22 + Math.random() * 0.05;
            const th = 0.02 + Math.random() * 0.02;
            const book = new THREE.Mesh(
                new THREE.BoxGeometry(w, th, h),
                new THREE.MeshStandardMaterial({
                    color: colors[Math.floor(Math.random() * colors.length)],
                    roughness: 0.7
                })
            );
            book.position.set(x, 0.42 + currentY + th / 2, z);
            book.rotation.y = (Math.random() - 0.5) * 0.5;
            book.castShadow = true;
            book.receiveShadow = true;
            this.group.add(book);
            this.obstacles.push(book);
            currentY += th;
        }
    }

    createMug(x, z) {
        const mugGroup = new THREE.Group();
        const body = new THREE.Mesh(
            new THREE.CylinderGeometry(0.04, 0.04, 0.1, 24),
            new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 })
        );
        body.position.y = 0.05;
        body.castShadow = true;
        mugGroup.add(body);

        // 把手
        const handle = new THREE.Mesh(
            new THREE.TorusGeometry(0.025, 0.005, 8, 16, Math.PI),
            new THREE.MeshStandardMaterial({ color: 0xffffff })
        );
        handle.position.set(0.04, 0.05, 0);
        handle.rotation.z = -Math.PI / 2;
        mugGroup.add(handle);

        mugGroup.position.set(x, 0.42, z);
        mugGroup.rotation.y = Math.random() * Math.PI;
        this.group.add(mugGroup);
        this.obstacles.push(body); // 只有杯身挡激光
    }



    createPlant(x, z) {
        const group = new THREE.Group();
        // 盆
        const pot = new THREE.Mesh(
            new THREE.CylinderGeometry(0.06, 0.04, 0.08, 16),
            new THREE.MeshStandardMaterial({ color: 0xc19a6b, roughness: 1.0 })
        );
        pot.position.y = 0.04;
        pot.castShadow = true;
        group.add(pot);
        // 土
        const soil = new THREE.Mesh(
            new THREE.CircleGeometry(0.055, 16),
            new THREE.MeshStandardMaterial({ color: 0x3d2817 })
        );
        soil.rotation.x = -Math.PI / 2;
        soil.position.y = 0.075;
        group.add(soil);
        // 叶子 (简单模拟)
        const leafGeo = new THREE.SphereGeometry(0.08, 8, 8);
        const leafMat = new THREE.MeshStandardMaterial({ color: 0x228b22, roughness: 0.6 });
        const leaf1 = new THREE.Mesh(leafGeo, leafMat);
        leaf1.position.set(0, 0.12, 0);
        leaf1.scale.set(1, 1.5, 1);
        group.add(leaf1);

        group.position.set(x, 0.42, z);
        this.group.add(group);
        this.obstacles.push(pot); // 盆挡激光
    }

    createDeskLamp(x, z) {
        const lamp = new THREE.Group();
        // Base
        const base = new THREE.Mesh(
            new THREE.CylinderGeometry(0.08, 0.09, 0.02, 24),
            new THREE.MeshStandardMaterial({ color: 0x333333 })
        );
        base.position.y = 0.01;
        base.castShadow = true;
        lamp.add(base);
        this.obstacles.push(base);

        // Arm
        const arm = new THREE.Mesh(
            new THREE.CylinderGeometry(0.01, 0.01, 0.3, 8),
            new THREE.MeshStandardMaterial({ color: 0xbbbbbb })
        );
        arm.position.y = 0.15;
        lamp.add(arm);

        // Shade
        const shade = new THREE.Mesh(
            new THREE.ConeGeometry(0.08, 0.12, 24, 1, true),
            new THREE.MeshStandardMaterial({ color: 0xdddddd, side: THREE.DoubleSide })
        );
        shade.position.set(0, 0.3, 0.05);
        shade.rotation.x = Math.PI / 4;
        shade.castShadow = true;
        lamp.add(shade);
        this.obstacles.push(shade);

        lamp.position.set(x, 0.42, z);
        this.group.add(lamp);
    }

    createTissueBox(x, z) {
        const box = new THREE.Mesh(
            new THREE.BoxGeometry(0.2, 0.1, 0.12),
            new THREE.MeshStandardMaterial({ color: 0xfffaf0 })
        );
        box.position.set(x, 0.42 + 0.05, z);
        box.castShadow = true;
        box.receiveShadow = true;
        this.group.add(box);
        this.obstacles.push(box);
    }

    createPaper(x, z) {
        const paper = new THREE.Mesh(
            new THREE.PlaneGeometry(0.21, 0.297),
            new THREE.MeshStandardMaterial({ color: 0xffffff, side: THREE.DoubleSide })
        );
        paper.rotation.x = -Math.PI / 2;
        paper.rotation.z = Math.random() * Math.PI;
        paper.position.set(x, 0.421, z); // slightly above desk
        paper.receiveShadow = true;
        this.group.add(paper);
    }

    // --- 目标物品 (Helper functions) ---
    addItem(name, mesh, position) {
        mesh.position.set(position.x, position.y + 0.42, position.z); // Adjust y for desk
        this.items.push({ name, mesh, position: mesh.position.clone() });
        this.group.add(mesh);
        this.obstacles.push(mesh); // 目标物品本身也是碰撞体
        return this;
    }



    createPhone(x, z) {
        const g = new THREE.Group();
        // 手机机身 - 增大约2倍
        const body = new THREE.Mesh(
            new THREE.BoxGeometry(0.12, 0.015, 0.22),
            new THREE.MeshStandardMaterial({ color: 0x1a1a1a, metalness: 0.6 })
        );
        body.castShadow = true;
        g.add(body);
        // 屏幕
        const screen = new THREE.Mesh(
            new THREE.PlaneGeometry(0.1, 0.18),
            new THREE.MeshBasicMaterial({ color: 0x222266 })
        );
        screen.rotation.x = -Math.PI / 2;
        screen.position.y = 0.008;
        g.add(screen);
        return this.addItem('手机', g, { x, y: 0.008, z });
    }

    createWallet(x, z) {
        const g = new THREE.Group();
        // 钱包 - 增大
        const wallet = new THREE.Mesh(
            new THREE.BoxGeometry(0.15, 0.025, 0.1),
            new THREE.MeshStandardMaterial({ color: 0x663300, roughness: 0.7 })
        );
        wallet.castShadow = true;
        g.add(wallet);

        // 钱包高度0.025 -> 中心Y=0.0125
        return this.addItem('钱包', g, { x, y: 0.0125, z });
    }





    createEarphones(x, z) {
        const g = new THREE.Group();
        const mat = new THREE.MeshStandardMaterial({ color: 0xffffff });
        // 耳机头 - 增大
        [-0.04, 0.04].forEach(xo => {
            const bud = new THREE.Mesh(new THREE.SphereGeometry(0.025, 12, 12), mat);
            bud.position.x = xo;
            bud.castShadow = true;
            g.add(bud);
        });
        // 连接线
        const wire = new THREE.Mesh(
            new THREE.CylinderGeometry(0.004, 0.004, 0.08, 8),
            mat
        );
        wire.rotation.z = Math.PI / 2;
        g.add(wire);
        return this.addItem('耳机', g, { x, y: 0.025, z });
    }

    createCharger(x, z) {
        const g = new THREE.Group();
        // 充电头 - 增大
        const head = new THREE.Mesh(
            new THREE.BoxGeometry(0.06, 0.045, 0.05),
            new THREE.MeshStandardMaterial({ color: 0xf0f0f0 })
        );
        head.castShadow = true;
        g.add(head);
        // 线缆
        const cable = new THREE.Mesh(
            new THREE.CylinderGeometry(0.006, 0.006, 0.15, 8),
            new THREE.MeshStandardMaterial({ color: 0xdddddd })
        );
        cable.position.set(0.1, 0, 0);
        cable.rotation.z = Math.PI / 2;
        g.add(cable);

        // 修正高度: 头高度0.045 -> 中心0.0225. 线直径0.012 -> 中心0.006.
        // 已经在中心添加，所以只需要抬高整个组
        return this.addItem('充电器', g, { x, y: 0.0225, z });
    }

    createRemote(x, z) {
        const g = new THREE.Group();
        // 遥控器主体 - 增大
        const body = new THREE.Mesh(
            new THREE.BoxGeometry(0.07, 0.025, 0.22),
            new THREE.MeshStandardMaterial({ color: 0x1a1a1a })
        );
        body.castShadow = true;
        g.add(body);
        // 按钮
        for (let i = 0; i < 6; i++) {
            const btn = new THREE.Mesh(
                new THREE.CylinderGeometry(0.008, 0.008, 0.004, 12),
                new THREE.MeshStandardMaterial({ color: i === 0 ? 0xff0000 : 0x444444 })
            );
            btn.position.set(0, 0.015, -0.07 + i * 0.025);
            g.add(btn);
        }
        return this.addItem('遥控器', g, { x, y: 0.015, z });
    }

    createPillBottle(x, z) {
        const g = new THREE.Group();
        // 药瓶 - 增大
        const bottle = new THREE.Mesh(
            new THREE.CylinderGeometry(0.035, 0.035, 0.08, 24),
            new THREE.MeshStandardMaterial({ color: 0xff6600, transparent: true, opacity: 0.85 })
        );
        bottle.castShadow = true;
        g.add(bottle);
        // 瓶盖
        const cap = new THREE.Mesh(
            new THREE.CylinderGeometry(0.037, 0.037, 0.02, 24),
            new THREE.MeshStandardMaterial({ color: 0xffffff })
        );
        cap.position.y = 0.05;
        g.add(cap);
        return this.addItem('药瓶', g, { x, y: 0.04, z });
    }

    createUSBDrive(x, z) {
        const g = new THREE.Group();
        // U盘主体 - 增大
        const body = new THREE.Mesh(
            new THREE.BoxGeometry(0.025, 0.012, 0.07),
            new THREE.MeshStandardMaterial({ color: 0x0066cc })
        );
        body.castShadow = true;
        g.add(body);
        // USB接口
        const usb = new THREE.Mesh(
            new THREE.BoxGeometry(0.02, 0.006, 0.025),
            new THREE.MeshStandardMaterial({ color: 0xcccccc, metalness: 0.8 })
        );
        usb.position.z = -0.045;
        g.add(usb);
        return this.addItem('U盘', g, { x, y: 0.005, z }); // 高度0.01 -> 中心0.005
    }

    createLipstick(x, z) {
        const g = new THREE.Group();
        // 口红 - 增大
        const tube = new THREE.Mesh(
            new THREE.CylinderGeometry(0.018, 0.018, 0.1, 16),
            new THREE.MeshStandardMaterial({ color: 0xcc2255, metalness: 0.6 })
        );
        tube.castShadow = true;
        g.add(tube);
        // 金色装饰
        const ring = new THREE.Mesh(
            new THREE.CylinderGeometry(0.02, 0.02, 0.008, 16),
            new THREE.MeshStandardMaterial({ color: 0xffd700, metalness: 0.9 })
        );
        ring.position.y = 0.03;
        g.add(ring);
        return this.addItem('口红', g, { x, y: 0.05, z });
    }



    clear() {
        // Remove old items from group
        // In a full implementation, we'd dispose geometries/materials
        while (this.group.children.length > 0) {
            this.group.remove(this.group.children[0]);
        }
        this.items = [];
        this.obstacles = [];
    }

    getItemPosition(name) {
        const item = this.items.find(i => i.name === name);
        return item ? item.position : null;
    }

    getItemMesh(name) {
        const item = this.items.find(i => i.name === name);
        return item ? item.mesh : null;
    }

    getColliders() {
        return this.obstacles;
    }

    getMesh() { return this.group; }
}

// ==================== 状态机 ====================
class StateMachine {
    constructor(cube) {
        this.cube = cube;
        this.currentMode = 'ambient';
        this.currentEmotion = 'calm';
        this.onModeChange = null;
    }

    switchToAmbient() {
        if (this.currentMode === 'ambient') return;
        this.currentMode = 'ambient';
        this.cube.breathing.setBreathing(true);
        this.cube.breathing.setEmotion(this.currentEmotion);
        this.cube.gimbal.lower();
        const config = EMOTION_CONFIG[this.currentEmotion];
        this.cube.led.setEmotion(this.currentEmotion, config.color);
        this.cube.setGlowColor(config.color);
        if (this.onModeChange) this.onModeChange('ambient');
    }

    switchToFocus() {
        if (this.currentMode === 'focus') return;
        this.currentMode = 'focus';
        this.cube.breathing.setBreathing(false);
        this.cube.gimbal.raise();
        // Focus下，默认LED显示focus图案
        this.cube.led.setEmotion('focus', 0x00ccff);
        this.cube.setGlowColor(0x00ccff);
        if (this.onModeChange) this.onModeChange('focus');
    }

    setEmotion(emotionKey) {
        // 将旧的key映射到新的6种情绪
        // 前端传来的可能是 'happy' (old) 或 'calm' (new)
        // 这里做一个简单的兼容映射
        const mapping = {
            'happy': 'excited', 'sleep': 'deepSleep', 'focus': 'calm',
            'music': 'relaxed', 'locate': 'anxious', 'arrow': 'meditative'
        };
        const key = mapping[emotionKey] || emotionKey;

        if (!EMOTION_CONFIG[key]) return;

        this.currentEmotion = key;

        if (this.currentMode === 'ambient') {
            const config = EMOTION_CONFIG[key];
            this.cube.breathing.setEmotion(key);
            this.cube.led.setEmotion(key, config.color);
            this.cube.setGlowColor(config.color);
        }
    }

    toggle() {
        if (this.currentMode === 'ambient') this.switchToFocus();
        else this.switchToAmbient();
    }

    getMode() { return this.currentMode; }
}

// ==================== 灵犀魔方主体 ====================
class SentientCube {
    constructor(scene, deskItems) {
        this.scene = scene;
        this.deskItems = deskItems;
        this.group = new THREE.Group();
        this.led = null;
        this.gimbal = null;
        this.breathing = null;
        this.glowMesh = null;
        this.init();
    }

    init() {
        // Core Cube
        const core = new THREE.Mesh(
            new THREE.BoxGeometry(0.12, 0.14, 0.12),
            new THREE.MeshStandardMaterial({ color: 0x8b7b6a, roughness: 0.9 })
        );
        core.castShadow = true;
        this.group.add(core);

        // Top cap & Hole
        const top = new THREE.Mesh(new THREE.BoxGeometry(0.11, 0.01, 0.11), new THREE.MeshStandardMaterial({ color: 0x2d2d2d }));
        top.position.y = 0.075;
        this.group.add(top);

        // LED
        this.led = new PhantomLED(16, 8);
        const ledMesh = this.led.getMesh();
        // 调整位置: z=0.061 (确保背板在魔方表面0.06之上)
        ledMesh.position.set(0, 0.01, 0.061);
        // removing scale (keep 1.0)
        ledMesh.scale.set(1.0, 1.0, 1);
        this.group.add(ledMesh);

        // Gimbal (传入deskItems用于射线检测)
        this.gimbal = new BionicGimbal(this.scene, this.deskItems);
        this.gimbal.getMesh().position.y = 0.07;
        this.group.add(this.gimbal.getMesh());
        this.gimbal.getSceneObjects().forEach(obj => this.scene.add(obj));

        // Breathing
        this.breathing = new BreathingSystem();
        this.group.add(this.breathing.getMesh());

        // Glow
        this.createGlowRing();

        this.led.setEmotion('calm', EMOTION_CONFIG.calm.color);
    }

    createGlowRing() {
        this.glowMesh = new THREE.Mesh(
            new THREE.TorusGeometry(0.085, 0.005, 8, 32),
            new THREE.MeshBasicMaterial({ color: 0xffaa44, transparent: true, opacity: 0.7 })
        );
        this.glowMesh.rotation.x = Math.PI / 2;
        this.glowMesh.position.y = -0.072;
        this.group.add(this.glowMesh);

        this.haloMesh = new THREE.Mesh(
            new THREE.TorusGeometry(0.09, 0.012, 8, 32),
            new THREE.MeshBasicMaterial({ color: 0xffaa44, transparent: true, opacity: 0.2 })
        );
        this.haloMesh.rotation.x = Math.PI / 2;
        this.haloMesh.position.y = -0.073;
        this.group.add(this.haloMesh);
    }

    setGlowColor(color) {
        if (this.glowMesh) this.glowMesh.material.color.setHex(color);
        if (this.haloMesh) this.haloMesh.material.color.setHex(color);
    }

    update(time, deltaTime) {
        this.breathing.update(time);
        this.gimbal.update(deltaTime, this.getWorldPosition());
        this.led.update(time);

        if (this.glowMesh) {
            const glow = 0.5 + 0.3 * Math.sin(time * 2);
            this.glowMesh.material.opacity = glow;
            if (this.haloMesh) this.haloMesh.material.opacity = glow * 0.3;
        }
    }

    getWorldPosition() {
        const pos = new THREE.Vector3();
        this.group.getWorldPosition(pos);
        return pos;
    }

    getMesh() { return this.group; }
}

// ==================== 主仿真类 ====================
class SentientCubeSimulation {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.cube = null;
        this.stateMachine = null;
        this.deskItems = null;
        this.clock = new THREE.Clock();

        this.init();
        this.createScene();
        this.createDesk();

        this.deskItems = new DeskItems();
        this.deskItems.generateClutteredDesk(); // 生成复杂桌面
        this.scene.add(this.deskItems.getMesh());

        this.createSentientCube();

        this.setupUI();
        this.hideLoading();
        this.animate();
    }

    init() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x1a1a2e);
        this.scene.fog = new THREE.Fog(0x1a1a2e, 4, 12);

        this.camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
        this.camera.position.set(1.2, 1.0, 1.5); // 更远视角以看到更大桌面
        this.camera.lookAt(0, 0.42, 0);

        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        document.getElementById('container').appendChild(this.renderer.domElement);

        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.target.set(0, 0.42, 0); // Focus on desk surface

        this.createLights();
        window.addEventListener('resize', () => this.onWindowResize());
    }

    createLights() {
        this.scene.add(new THREE.AmbientLight(0xffffff, 0.4));

        // 主光，产生阴影
        const main = new THREE.DirectionalLight(0xffeedd, 1.0);
        main.position.set(2, 4, 3);
        main.castShadow = true;
        main.shadow.mapSize.set(2048, 2048);
        main.shadow.bias = -0.0001;
        this.scene.add(main);

        // 补光
        this.scene.add(new THREE.DirectionalLight(0x88ccff, 0.3).translateX(-2).translateY(2));
    }

    createScene() {
        // Floor
        const floor = new THREE.Mesh(new THREE.PlaneGeometry(10, 10), new THREE.MeshStandardMaterial({ color: 0x222233 }));
        floor.rotation.x = -Math.PI / 2;
        floor.receiveShadow = true;
        this.scene.add(floor);
    }

    createDesk() {
        const desk = new THREE.Group();
        // Desk Top
        const top = new THREE.Mesh(
            new THREE.BoxGeometry(2.0, 0.03, 1.4),
            new THREE.MeshStandardMaterial({ color: 0x5d4e37, roughness: 0.6 })
        );
        top.position.y = 0.42;
        top.receiveShadow = true;
        top.castShadow = true;
        desk.add(top);

        // Legs
        [[-0.9, -0.6], [0.9, -0.6], [-0.9, 0.6], [0.9, 0.6]].forEach(([x, z]) => {
            const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.42), new THREE.MeshStandardMaterial({ color: 0x333333 }));
            leg.position.set(x, 0.21, z);
            leg.castShadow = true;
            desk.add(leg);
        });
        this.scene.add(desk);
    }

    createSentientCube() {
        this.cube = new SentientCube(this.scene, this.deskItems);
        this.cube.getMesh().position.set(0, 0.51, 0); // At center of desk
        this.scene.add(this.cube.getMesh());

        this.stateMachine = new StateMachine(this.cube);
        this.stateMachine.onModeChange = m => this.updateUIForMode(m);
    }

    async api(path, options = {}) {
        const res = await fetch(`/api${path}`, {
            headers: { 'Content-Type': 'application/json' },
            ...options
        });
        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            throw new Error(data.error || `HTTP ${res.status}`);
        }
        return res.json();
    }

    applyBackendStatus(payload) {
        if (!payload) return;
        const mode = payload.mode || this.stateMachine?.getMode?.();
        if (mode) this.updateUIForMode(mode);
        if (payload.status) {
            this.updateStatus('gimbal', payload.status.gimbal);
            this.updateStatus('laser', payload.status.laser);
            this.updateStatus('breath', payload.status.breath);
        }
        if (payload.lastResponse) {
            this.setAssistantReply(payload.lastResponse);
        }
    }

    setAssistantReply(text) {
        const el = document.getElementById('assistant-reply');
        if (el && text) el.textContent = text;
    }

    async refreshReminders() {
        const list = document.getElementById('reminder-list');
        if (!list) return;
        try {
            const data = await this.api('/reminders');
            list.innerHTML = '';
            const reminders = data.reminders || [];
            if (reminders.length === 0) {
                const li = document.createElement('li');
                li.textContent = '暂无提醒';
                list.appendChild(li);
                return;
            }
            reminders.forEach(r => {
                const li = document.createElement('li');
                const time = new Date(r.remindAt).toLocaleString();
                li.textContent = `${time} · ${r.content} (${r.status})`;
                list.appendChild(li);
            });
        } catch (error) {
            this.setAssistantReply(`提醒加载失败: ${error.message}`);
        }
    }

    setupUI() {
        document.getElementById('mode-toggle')?.addEventListener('click', async () => {
            this.stateMachine.toggle();
            try {
                const mode = this.stateMachine.getMode();
                const status = await this.api('/mode', {
                    method: 'POST',
                    body: JSON.stringify({ mode })
                });
                this.applyBackendStatus(status);
            } catch (error) {
                this.setAssistantReply(`模式切换失败: ${error.message}`);
            }
        });

        document.querySelectorAll('.item-btn').forEach(btn => {
            btn.addEventListener('click', () => this.locateItem(btn.dataset.item));
        });

        // 新的情绪按钮逻辑
        document.querySelectorAll('.emotion-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const emotion = btn.dataset.emotion; // calm, anxious, etc.
                this.stateMachine.setEmotion(emotion);
                try {
                    const status = await this.api('/emotion', {
                        method: 'POST',
                        body: JSON.stringify({ emotion })
                    });
                    this.applyBackendStatus(status);
                } catch (error) {
                    this.setAssistantReply(`情绪切换失败: ${error.message}`);
                }
            });
        });

        const exportBtn = document.getElementById('export-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportGLB());
        }

        document.getElementById('command-btn')?.addEventListener('click', async () => {
            const input = document.getElementById('command-input');
            const text = input?.value?.trim();
            if (!text) return;
            try {
                const data = await this.api('/command', {
                    method: 'POST',
                    body: JSON.stringify({ text })
                });
                this.applyBackendStatus(data);
                this.updateUIForMode(data.mode);
                input.value = '';
                await this.refreshReminders();
            } catch (error) {
                this.setAssistantReply(`指令执行失败: ${error.message}`);
            }
        });

        document.getElementById('reminder-btn')?.addEventListener('click', async () => {
            const timeInput = document.getElementById('reminder-time');
            const contentInput = document.getElementById('reminder-content');
            const timeText = timeInput?.value?.trim();
            const content = contentInput?.value?.trim();
            if (!timeText || !content) return;
            try {
                await this.api('/reminders', {
                    method: 'POST',
                    body: JSON.stringify({ timeText, content })
                });
                this.setAssistantReply(`已添加提醒：${timeText} ${content}`);
                timeInput.value = '';
                contentInput.value = '';
                await this.refreshReminders();
            } catch (error) {
                this.setAssistantReply(`添加提醒失败: ${error.message}`);
            }
        });
    }

    async locateItem(itemName) {
        this.stateMachine.switchToFocus();
        const itemPos = this.deskItems.getItemPosition(itemName);
        const itemMesh = this.deskItems.getItemMesh(itemName);
        if (!itemPos) return;

        // 设置目标物品mesh用于遮挡检测
        this.cube.gimbal.targetMesh = itemMesh;

        const cubePos = this.cube.getWorldPosition();
        this.updateStatus('gimbal', '定位中');
        this.cube.led.setEmotion('locate', 0xffaa00);
        try {
            const data = await this.api('/find', {
                method: 'POST',
                body: JSON.stringify({ name: itemName })
            });
            this.applyBackendStatus(data);
        } catch (error) {
            this.setAssistantReply(`寻物失败: ${error.message}`);
        }

        setTimeout(() => {
            // 云台动作
            this.cube.gimbal.pointToPosition(itemPos, cubePos);

            setTimeout(() => {
                // 开激光
                this.cube.gimbal.setLaser(true);

                // 检查是否被遮挡
                if (this.cube.gimbal.targetBlocked) {
                    this.cube.led.setEmotion('error', 0xff4444);
                    this.updateStatus('laser', '被遮挡');
                    this.updateStatus('gimbal', '目标不可见');
                } else {
                    this.cube.led.showSuccess(0x00ff88);
                    this.updateStatus('laser', '照射中');
                    this.updateStatus('gimbal', '锁定目标');
                }

                setTimeout(() => {
                    // 复位
                    this.cube.gimbal.setLaser(false);
                    this.cube.gimbal.targetMesh = null;
                    this.cube.led.setEmotion('focus', 0x00ccff);
                    this.updateStatus('laser', '关闭');
                    this.updateStatus('gimbal', '待命');
                }, 5000);
            }, 700);
        }, 500);
    }

    updateStatus(type, value) {
        const el = document.getElementById(`${type}-status`);
        if (el && typeof value === 'string') el.textContent = value;
    }

    updateUIForMode(mode) {
        const body = document.body;
        const toggle = document.getElementById('mode-toggle');
        const label = document.getElementById('mode-label');

        if (mode === 'ambient') {
            body.classList.replace('focus-mode', 'ambient-mode');
            if (toggle) toggle.textContent = '🟢 右脑模式';
            if (label) label.textContent = '感性伴侣 · Ambient';
            this.updateStatus('gimbal', '收起');
            this.updateStatus('laser', '关闭');
            this.updateStatus('breath', '运行中');
        } else {
            body.classList.replace('ambient-mode', 'focus-mode');
            if (toggle) toggle.textContent = '🔵 左脑模式';
            if (label) label.textContent = '理性助理 · Focus';
            this.updateStatus('gimbal', '升起');
            this.updateStatus('breath', '暂停');
        }
    }

    exportGLB() {
        const exporter = new GLTFExporter();
        const options = {
            binary: true,
            onlyVisible: true,
            truncateDrawRange: true
        };

        // Export only the cube group
        exporter.parse(
            this.cube.getMesh(),
            (glb) => {
                const blob = new Blob([glb], { type: 'application/octet-stream' });
                const link = document.createElement('a');
                link.style.display = 'none';
                document.body.appendChild(link);
                link.href = URL.createObjectURL(blob);
                link.download = 'sentient_cube_model.glb';
                link.click();
                document.body.removeChild(link);
            },
            (err) => {
                console.error('An error happened during export:', err);
                alert('导出失败，请查看控制台错误信息');
            },
            options
        );
    }

    hideLoading() {
        const loading = document.getElementById('loading');
        if (loading) setTimeout(() => loading.classList.add('hidden'), 500);
        this.stateMachine.switchToAmbient();
        this.api('/status')
            .then(data => this.applyBackendStatus(data))
            .catch(() => { });
        this.refreshReminders();
    }

    onWindowResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        const time = this.clock.getElapsedTime();
        const dt = this.clock.getDelta();
        if (this.cube) this.cube.update(time, dt);
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }
}

// 启动
document.addEventListener('DOMContentLoaded', () => new SentientCubeSimulation());
