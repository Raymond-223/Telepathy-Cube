import time
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.collections import LineCollection
from matplotlib.patches import Circle, Wedge, Rectangle, Ellipse, Polygon, FancyBboxPatch
from matplotlib.widgets import Slider, Button, RadioButtons
import matplotlib.gridspec as gridspec
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap, to_rgba
import warnings

warnings.filterwarnings('ignore')


class EnhancedSentientBreath:
    def __init__(self):
        # 呼吸参数
        self.servo_min = 30
        self.servo_max = 60
        self.cycle_duration = 4.0
        self.smoothness = 0.03
        self.start_time = time.time()

        # 数据存储
        self.time_history = []
        self.angle_history = []
        self.wave_history = []
        self.phase_history = []
        self.max_history = 300

        # 状态变量
        self.running = True
        self.current_phase = 0
        self.current_emotion = "Calm"
        self.breath_count = 0
        self.emotion_colors = {}
        
        # 存储每个情绪的参数状态 {emotion_name: {duration, min, max}}
        self.emotion_params = {}

        # UI Elements
        self.panel_bg = None
        self.border = None
        self.control_text = None

        # 颜色和样式
        self.setup_colors()

        # 初始化情绪参数状态
        self.init_emotion_params()

        # 初始化图形
        self.setup_visualization()

        # 设置交互控件
        self.setup_controls()

        # 平滑过渡变量
        self.target_cycle_duration = self.cycle_duration
        self.target_servo_min = self.servo_min
        self.target_servo_max = self.servo_max
        # 初始颜色 (RGB)
        self.current_r, self.current_g, self.current_b = to_rgba(self.emotion_colors[self.current_emotion])[:3]
        self.target_r, self.target_g, self.target_b = self.current_r, self.current_g, self.current_b
        
        self.transition_speed = 0.03  # 过渡速度因子
        self.last_update_time = time.time()
        self.accumulated_phase = 0.0  # 累积相位

    def setup_colors(self):
        """设置颜色方案"""
        self.colors = {
            'primary': '#FF6B6B',  # 珊瑚红
            'secondary': '#4ECDC4',  # 青色
            'accent': '#FFD166',  # 金黄色
            'background': '#0A0E17',  # 深蓝背景
            'panel': '#1A1F2E',  # 面板背景
            'text': '#FFFFFF',  # 白色文字
            'subtext': '#A0AEC0',  # 灰色文字
            'wave': '#00FFAB',  # 亮绿色波形
            'history': '#FF9E6D',  # 橙色历史
            'petal1': '#FF6B6B',  # 花瓣颜色1
            'petal2': '#45B7D1',  # 花瓣颜色2
            'petal3': '#96CEB4',  # 花瓣颜色3
            'petal4': '#FFEAA7',  # 花瓣颜色4
            'petal5': '#DDA0DD',  # 花瓣颜色5
            'petal6': '#4ECDC4',  # 花瓣颜色6
        }

        # 情绪颜色映射
        self.emotion_colors = {
            "Calm": "#4ECDC4",  # 青色
            "Anxious": "#FF6B6B",  # 红色
            "Relaxed": "#96CEB4",  # 浅绿
            "Excited": "#FFD166",  # 黄色
            "Deep Sleep": "#7B68EE",  # 紫色
            "Meditative": "#9370DB",  # 淡紫
        }

        # 创建自定义渐变colormap
        self.wave_cmap = LinearSegmentedColormap.from_list(
            'wave_gradient', ['#0A0E17', '#00FFAB', '#4ECDC4']
        )

        # 设置matplotlib样式
        plt.style.use('dark_background')

    def init_emotion_params(self):
        """初始化所有情绪的参数状态"""
        emotions = ["Calm", "Anxious", "Relaxed", "Excited", "Deep Sleep", "Meditative"]
        for emotion in emotions:
            params = self.get_emotional_params(emotion)
            # 从 get_emotional_params 获取的参数转换为内部存储格式
            self.emotion_params[emotion] = {
                "cycle_duration": params["duration"],
                "servo_min": params["min_angle"],
                "servo_max": params["max_angle"]
            }

    def get_biological_wave(self, phase_progress):
        """增强的生物呼吸波形生成器 (基于相位 0.0-1.0)"""
        phase = phase_progress * 2 * math.pi

        # 使用组合波形创造更自然的呼吸
        wave1 = math.exp(math.sin(phase)) - (1 / math.e)  # 主波形
        wave2 = 0.3 * math.sin(phase * 2)  # 次要谐波
        wave3 = 0.1 * math.sin(phase * 3 + 0.5)  # 更细微的变化

        raw_value = wave1 + wave2 + wave3
        normalized = raw_value / (math.e - (1 / math.e) + 0.3 + 0.1)

        return max(0.0, min(1.0, normalized))

    def get_emotional_params(self, emotion):
        """根据情绪返回参数"""
        emotions = {
            "Calm": {"duration": 4.0, "min_angle": 30, "max_angle": 60, "color": "#4ECDC4"},
            "Anxious": {"duration": 2.0, "min_angle": 40, "max_angle": 80, "color": "#FF6B6B"},
            "Relaxed": {"duration": 6.0, "min_angle": 20, "max_angle": 50, "color": "#96CEB4"},
            "Excited": {"duration": 1.5, "min_angle": 50, "max_angle": 90, "color": "#FFD166"},
            "Deep Sleep": {"duration": 8.0, "min_angle": 10, "max_angle": 40, "color": "#7B68EE"},
            "Meditative": {"duration": 10.0, "min_angle": 15, "max_angle": 45, "color": "#9370DB"},
        }
        return emotions.get(emotion, emotions["Calm"])

    def setup_visualization(self):
        """设置高级可视化界面"""
        self.fig = plt.figure(figsize=(16, 10), facecolor=self.colors['background'])

        # 使用GridSpec创建复杂布局
        gs = gridspec.GridSpec(12, 12, figure=self.fig,
                               hspace=0.8, wspace=0.8,
                               left=0.05, right=0.95,
                               top=0.95, bottom=0.05)

        # 1. 主呼吸器官显示（左上）
        self.ax_organ = plt.subplot(gs[0:6, 0:4])
        self.setup_organ_display()

        # 2. 波形图（右上）
        self.ax_wave = plt.subplot(gs[0:4, 4:12])
        self.setup_wave_display()

        # 3. 3D波形表面图（中右）
        self.ax_surface = plt.subplot(gs[4:8, 4:12], projection='3d')
        self.setup_surface_display()

        # 4. 参数面板（左下）
        self.ax_params = plt.subplot(gs[6:12, 0:4])
        self.setup_params_display()

        # 5. 历史图表（右下）
        self.ax_history = plt.subplot(gs[8:12, 4:12])
        self.setup_history_display()

        # 添加标题
        self.fig.suptitle('Enhanced Sentient Breath Visualization',
                          fontsize=20, color=self.colors['accent'],
                          fontweight='bold', y=0.98)

        # 添加装饰性元素
        self.add_decoration()

        # 添加情绪指示器
        self.add_emotion_indicator()

    def setup_organ_display(self):
        """设置呼吸器官显示"""
        self.ax_organ.set_xlim(-2, 2)
        self.ax_organ.set_ylim(-2, 2)
        self.ax_organ.set_aspect('equal')
        self.ax_organ.axis('off')

        # 背景圆形
        self.organ_bg = Circle((0, 0), 1.8,
                               facecolor=self.colors['panel'],
                               edgecolor=self.emotion_colors[self.current_emotion],
                               linewidth=3, alpha=0.7)
        self.ax_organ.add_patch(self.organ_bg)

        # 创建8个花瓣（更自然）
        self.petals = []
        petal_colors = [self.colors[f'petal{i}'] for i in range(1, 7)]

        for i in range(8):
            angle = i * 45  # 8个花瓣，每个45度
            # 创建更自然的花瓣形状
            theta1 = angle - 15
            theta2 = angle + 15

            # 使用楔形创建花瓣
            petal = Wedge((0, 0), 1.5, theta1, theta2,
                          width=0.5,
                          facecolor=petal_colors[i % len(petal_colors)],
                          edgecolor='white',
                          linewidth=1.5,
                          alpha=0.8)
            self.petals.append(self.ax_organ.add_patch(petal))

        # 中心核心
        self.organ_core = Circle((0, 0), 0.4,
                                 facecolor=self.emotion_colors[self.current_emotion],
                                 edgecolor='white',
                                 linewidth=2,
                                 alpha=0.9)
        self.ax_organ.add_patch(self.organ_core)

        # 内部光环
        self.inner_ring = Circle((0, 0), 0.6,
                                 facecolor='none',
                                 edgecolor=self.emotion_colors[self.current_emotion],
                                 linewidth=3,
                                 alpha=0.5,
                                 linestyle='--')
        self.ax_organ.add_patch(self.inner_ring)

        # 外部光环
        self.outer_ring = Circle((0, 0), 1.2,
                                 facecolor='none',
                                 edgecolor=self.emotion_colors[self.current_emotion],
                                 linewidth=2,
                                 alpha=0.3,
                                 linestyle=':')
        self.ax_organ.add_patch(self.outer_ring)

        # 标题
        self.organ_title = self.ax_organ.set_title(f'BREATHING ORGAN - {self.current_emotion}',
                                                   fontsize=14,
                                                   color=self.emotion_colors[self.current_emotion],
                                                   pad=20,
                                                   fontweight='bold')

    def setup_wave_display(self):
        """设置波形显示"""
        self.ax_wave.clear()
        self.ax_wave.set_facecolor(self.colors['panel'])

        # 设置网格
        self.ax_wave.grid(True, alpha=0.2, linestyle='--', color=self.colors['subtext'])

        # 设置坐标轴颜色
        self.ax_wave.spines['bottom'].set_color(self.colors['subtext'])
        self.ax_wave.spines['left'].set_color(self.colors['subtext'])
        self.ax_wave.tick_params(colors=self.colors['subtext'])

        # 创建波形线
        self.wave_line, = self.ax_wave.plot([], [],
                                            color=self.emotion_colors[self.current_emotion],
                                            linewidth=3,
                                            alpha=0.9,
                                            label=f'{self.current_emotion} Wave')

        # 创建填充区域
        self.wave_fill = self.ax_wave.fill_between([], [],
                                                   color=self.emotion_colors[self.current_emotion],
                                                   alpha=0.2)

        # 当前点标记
        self.current_point, = self.ax_wave.plot([], [],
                                                'o',
                                                color=self.emotion_colors[self.current_emotion],
                                                markersize=12,
                                                markeredgecolor='white',
                                                markeredgewidth=2)

        # 设置标签和标题
        self.ax_wave.set_xlabel('Time (s)', fontsize=11, color=self.colors['text'])
        self.ax_wave.set_ylabel('Intensity', fontsize=11, color=self.colors['text'])
        self.wave_title = self.ax_wave.set_title(f'BREATH WAVEFORM - {self.current_emotion}',
                                                 fontsize=14,
                                                 color=self.emotion_colors[self.current_emotion],
                                                 fontweight='bold',
                                                 pad=15)

        # 添加图例
        self.ax_wave.legend(loc='upper right',
                            framealpha=0.7,
                            facecolor=self.colors['background'])

        # 设置范围
        self.ax_wave.set_xlim(0, 10)
        self.ax_wave.set_ylim(-0.1, 1.1)

    def setup_surface_display(self):
        """设置3D波形表面显示"""
        self.ax_surface.clear()
        self.ax_surface.set_facecolor(self.colors['background'])

        # 创建初始表面数据
        x = np.linspace(0, 2 * np.pi, 50)
        y = np.linspace(0, 1, 20)
        X, Y = np.meshgrid(x, y)
        Z = np.sin(X) * Y

        # 创建表面图
        self.surface_plot = self.ax_surface.plot_surface(
            X, Y, Z,
            cmap='viridis',
            alpha=0.8,
            linewidth=0.1,
            antialiased=True
        )

        # 设置3D视图
        self.ax_surface.view_init(elev=30, azim=45)
        self.ax_surface.set_xlabel('Phase', fontsize=9, color=self.colors['text'])
        self.ax_surface.set_ylabel('Amplitude', fontsize=9, color=self.colors['text'])
        self.ax_surface.set_zlabel('Value', fontsize=9, color=self.colors['text'])

        # 设置标题
        self.surface_title = self.ax_surface.set_title(f'3D WAVE SURFACE - {self.current_emotion}',
                                                       fontsize=14,
                                                       color=self.emotion_colors[self.current_emotion],
                                                       fontweight='bold',
                                                       pad=20)

        # 移除背景网格（可选）
        self.ax_surface.grid(False)

    def setup_params_display(self):
        """设置参数显示面板"""
        self.ax_params.clear()
        self.ax_params.axis('off')

        # 创建面板背景
        self.panel_bg = FancyBboxPatch((0, 0), 1, 1,
                                  boxstyle="round,pad=0.02",
                                  facecolor=self.colors['panel'],
                                  edgecolor=self.emotion_colors[self.current_emotion],
                                  linewidth=2,
                                  alpha=0.9)
        self.ax_params.add_patch(self.panel_bg)

        # 标题
        self.params_title = self.ax_params.text(0.5, 0.95, f'STATUS PANEL - {self.current_emotion}',
                                                fontsize=16,
                                                color=self.emotion_colors[self.current_emotion],
                                                ha='center',
                                                va='top',
                                                fontweight='bold')

        # 状态数据文本
        self.status_texts = []
        status_y = 0.85
        status_dy = 0.12

        status_items = [
            ("Emotion:", self.current_emotion, self.emotion_colors[self.current_emotion]),
            ("Cycle Time:", f"{self.cycle_duration:.1f} s", self.colors['secondary']),
            ("Angle Range:", f"{self.servo_min}° - {self.servo_max}°", self.colors['primary']),
            ("Breath Count:", "0", self.colors['accent']),
            ("Phase:", "0.0%", self.colors['wave']),
            ("Current Angle:", "30.0°", self.colors['history']),
            ("Breath Rate:", f"{60 / self.cycle_duration:.1f} BPM", self.colors['petal4']),
        ]

        for label, value, color in status_items:
            # 标签
            self.ax_params.text(0.1, status_y, label,
                                fontsize=11,
                                color=self.colors['subtext'],
                                ha='left',
                                va='center')

            # 值（动态更新）
            text_obj = self.ax_params.text(0.7, status_y, value,
                                           fontsize=12,
                                           color=color,
                                           ha='right',
                                           va='center',
                                           fontweight='bold')
            self.status_texts.append(text_obj)
            status_y -= status_dy

        # 呼吸阶段指示器
        self.phase_indicator = Circle((0.5, 0.15), 0.06,
                                      facecolor=self.emotion_colors[self.current_emotion],
                                      edgecolor='white',
                                      linewidth=2,
                                      alpha=0.8)
        self.ax_params.add_patch(self.phase_indicator)

        # 呼吸阶段文本
        self.breath_phase_text = self.ax_params.text(0.5, 0.05, 'INHALING',
                                                     fontsize=13,
                                                     color=self.emotion_colors[self.current_emotion],
                                                     ha='center',
                                                     va='center',
                                                     fontweight='bold')

        # 进度条背景
        progress_bg = Rectangle((0.25, 0.22), 0.5, 0.03,
                                facecolor=self.colors['background'],
                                edgecolor=self.colors['subtext'],
                                linewidth=1)
        self.ax_params.add_patch(progress_bg)

        # 进度条前景
        self.progress_fg = Rectangle((0.25, 0.22), 0, 0.03,
                                     facecolor=self.emotion_colors[self.current_emotion],
                                     alpha=0.8)
        self.ax_params.add_patch(self.progress_fg)

        # 情绪颜色指示器
        self.emotion_color_indicator = Rectangle((0.85, 0.9), 0.1, 0.03,
                                                 facecolor=self.emotion_colors[self.current_emotion],
                                                 edgecolor='white',
                                                 linewidth=1)
        self.ax_params.add_patch(self.emotion_color_indicator)

    def setup_history_display(self):
        """设置历史数据显示"""
        self.ax_history.clear()
        self.ax_history.set_facecolor(self.colors['panel'])

        # 设置网格
        self.ax_history.grid(True, alpha=0.2, linestyle=':', color=self.colors['subtext'])

        # 创建历史线
        self.history_line, = self.ax_history.plot([], [],
                                                  color=self.emotion_colors[self.current_emotion],
                                                  linewidth=2,
                                                  alpha=0.9,
                                                  label=f'{self.current_emotion} History')

        # 创建填充区域
        self.history_fill = self.ax_history.fill_between([], [],
                                                         color=self.emotion_colors[self.current_emotion],
                                                         alpha=0.2)

        # 设置标签和标题
        self.ax_history.set_xlabel('Time Points', fontsize=11, color=self.colors['text'])
        self.ax_history.set_ylabel('Servo Angle (°)', fontsize=11, color=self.colors['text'])
        self.history_title = self.ax_history.set_title(f'ANGLE HISTORY - {self.current_emotion}',
                                                       fontsize=14,
                                                       color=self.emotion_colors[self.current_emotion],
                                                       fontweight='bold',
                                                       pad=15)

        # 添加图例
        self.ax_history.legend(loc='upper right',
                               framealpha=0.7,
                               facecolor=self.colors['background'])

        # 设置范围
        self.ax_history.set_xlim(0, self.max_history)
        self.ax_history.set_ylim(self.servo_min - 10, self.servo_max + 10)

        # 添加参考线
        self.ax_history.axhline(y=self.servo_min, color=self.colors['subtext'],
                                linestyle='--', alpha=0.5, linewidth=1)
        self.ax_history.axhline(y=self.servo_max, color=self.colors['subtext'],
                                linestyle='--', alpha=0.5, linewidth=1)

    def add_decoration(self):
        """添加装饰性元素"""
        # 在整个图形周围添加边框
        self.border = FancyBboxPatch((0, 0), 1, 1,
                                transform=self.fig.transFigure,
                                boxstyle="round,pad=0.02",
                                facecolor='none',
                                edgecolor=self.emotion_colors[self.current_emotion],
                                linewidth=3,
                                alpha=0.5)
        self.fig.patches.append(self.border)

    def add_emotion_indicator(self):
        """添加情绪状态指示器"""
        # 在图形底部添加情绪指示器
        self.emotion_indicator_ax = self.fig.add_axes([0.3, 0.01, 0.4, 0.04])
        self.emotion_indicator_ax.set_facecolor(self.colors['background'])
        self.emotion_indicator_ax.axis('off')

        # 创建情绪状态条
        emotions = ["Calm", "Anxious", "Relaxed", "Excited", "Deep Sleep", "Meditative"]
        x_positions = np.linspace(0, 1, len(emotions))

        for i, (emotion, x) in enumerate(zip(emotions, x_positions)):
            color = self.emotion_colors[emotion]
            is_active = (emotion == self.current_emotion)

            # 情绪点
            marker_size = 10 if is_active else 6
            alpha = 1.0 if is_active else 0.5
            self.emotion_indicator_ax.plot(x, 0.5, 'o',
                                           color=color,
                                           markersize=marker_size,
                                           alpha=alpha)

            # 情绪标签
            fontweight = 'bold' if is_active else 'normal'
            self.emotion_indicator_ax.text(x, 0.2, emotion,
                                           fontsize=8,
                                           color=color,
                                           ha='center',
                                           va='center',
                                           fontweight=fontweight)

        # 当前情绪高亮
        self.current_emotion_marker, = self.emotion_indicator_ax.plot(
            x_positions[emotions.index(self.current_emotion)], 0.5, 'o',
            color=self.emotion_colors[self.current_emotion],
            markersize=14,
            markeredgecolor='white',
            markeredgewidth=2
        )

    def setup_controls(self):
        """设置交互控件"""
        # 创建控件区域
        controls_ax = self.fig.add_axes([0.02, 0.02, 0.25, 0.12])
        controls_ax.set_facecolor(self.colors['panel'])
        controls_ax.axis('off')

        # 控件标题
        controls_ax.text(0.5, 0.9, 'CONTROLS',
                         fontsize=12,
                         color=self.emotion_colors[self.current_emotion],
                         ha='center',
                         va='top',
                         fontweight='bold')

        # 控制说明文本
        controls_info = [
            "Space: Pause/Resume",
            "R: Reset Simulation",
            "+/-: Change Speed",
            "↑/↓: Adjust Range",
            "1-6: Emotion Presets",
            "C: Toggle 3D View",
        ]

        for i, text in enumerate(controls_info):
            controls_ax.text(0.05, 0.7 - i * 0.15, text,
                             fontsize=9,
                             color=self.colors['subtext'],
                             ha='left',
                             va='center')

        # 当前情绪显示
        # 当前情绪显示
        self.control_text = controls_ax.text(0.05, 0.9, f"Current: {self.current_emotion}",
                         fontsize=10,
                         color=self.emotion_colors[self.current_emotion],
                         ha='left',
                         va='top',
                         fontweight='bold')

    def update_visualization(self, frame):
        """更新所有可视化元素"""
        if not self.running:
            # 即使暂停也要更新时间戳，防止恢复时跳跃
            self.last_update_time = time.time()
            return []

        # 计算时间增量
        current_real_time = time.time()
        dt = current_real_time - self.last_update_time
        self.last_update_time = current_real_time
        
        # 限制最大dt以防卡顿导致的大跳跃
        if dt > 0.1: dt = 0.1

        # 1. 平滑过渡参数
        self.cycle_duration += (self.target_cycle_duration - self.cycle_duration) * self.transition_speed
        self.servo_min += (self.target_servo_min - self.servo_min) * self.transition_speed
        self.servo_max += (self.target_servo_max - self.servo_max) * self.transition_speed
        
        # 颜色平滑过渡
        self.current_r += (self.target_r - self.current_r) * self.transition_speed
        self.current_g += (self.target_g - self.current_g) * self.transition_speed
        self.current_b += (self.target_b - self.current_b) * self.transition_speed
        current_color = (self.current_r, self.current_g, self.current_b)
        
        # 2. 更新相位 (基于累积量，避免改变周期时的跳跃)
        self.accumulated_phase += dt / self.cycle_duration
        self.current_phase = self.accumulated_phase % 1.0
        
        # 3. 计算波形和角度
        wave = self.get_biological_wave(self.current_phase)
        angle = self.servo_min + (self.servo_max - self.servo_min) * wave

        # 检测呼吸完成（用于计数）
        if len(self.phase_history) > 1:
            if self.phase_history[-2] > 0.9 and self.current_phase < 0.1:
                self.breath_count += 1

        # 传递 current_color 给各组件更新函数
        eff_time = current_real_time - self.start_time # 使用连续时间，避免改变周期时跳跃

        # 1. 更新呼吸器官
        self.update_organ_display(wave, eff_time, current_color)

        # 2. 更新波形图
        self.update_wave_display(eff_time, wave, current_color)

        # 3. 更新3D表面
        self.update_surface_display(eff_time, current_color)

        # 4. 更新参数面板
        self.update_params_display(wave, angle, eff_time, current_color)

        # 5. 更新历史图表
        self.update_history_display(angle, current_color)

        # 6. 更新情绪指示器
        self.update_emotion_indicator()

        # 存储相位历史
        self.phase_history.append(self.current_phase)
        if len(self.phase_history) > 100:
            self.phase_history.pop(0)

        return []

    def update_organ_display(self, wave, current_time, current_color):
        """更新呼吸器官显示"""
        # emotion_color = self.emotion_colors[self.current_emotion] 
        # 使用传入的插值颜色
        emotion_color = current_color

        # 更新背景边框颜色
        self.organ_bg.set_edgecolor(emotion_color)

        # 更新花瓣大小和颜色
        for i, petal in enumerate(self.petals):
            # 每个花瓣有相位偏移
            phase_offset = i * 0.1
            # 使用新的phase参数调用
            local_phase = (self.accumulated_phase + phase_offset) % 1.0
            petal_wave = self.get_biological_wave(local_phase)

            # 花瓣宽度随呼吸变化
            width = 0.3 + 0.3 * petal_wave
            petal.set_width(width)

            # 花瓣颜色渐变（基于情绪颜色）
            # r, g, b = to_rgba(emotion_color)[:3] # current_color 已经是 rgb tuple
            r, g, b = current_color
            brightness = 0.7 + 0.3 * petal_wave
            petal.set_facecolor((r * brightness, g * brightness, b * brightness, 0.8))

            # 轻微旋转效果
            rotation = math.sin(current_time + i) * 5
            petal.set_theta1(petal.theta1 + rotation * 0.01)
            petal.set_theta2(petal.theta2 + rotation * 0.01)

        # 更新核心大小和颜色
        core_pulse = 0.4 + 0.1 * math.sin(current_time * 10)
        self.organ_core.set_radius(core_pulse)
        self.organ_core.set_facecolor(emotion_color)

        # 更新光环
        ring_pulse = 1.2 + 0.3 * wave
        self.outer_ring.set_radius(ring_pulse)
        self.outer_ring.set_edgecolor(emotion_color)
        self.inner_ring.set_edgecolor(emotion_color)

        # 内光环旋转 (Circle不支持theta rotation，暂时注释掉以修复Crash)
        # self.inner_ring.set_theta1(self.inner_ring.theta1 + 0.5)
        # self.inner_ring.set_theta2(self.inner_ring.theta2 + 0.5)

        # 更新标题
        self.organ_title.set_text(f'BREATHING ORGAN - {self.current_emotion}')
        self.organ_title.set_color(emotion_color)

    def update_wave_display(self, current_time, wave, current_color):
        """更新波形显示"""
        emotion_color = current_color

        # 更新历史数据
        self.time_history.append(current_time)
        self.wave_history.append(wave)

        # 只保留最近10秒的数据
        while self.time_history and current_time - self.time_history[0] > 10:
            self.time_history.pop(0)
            self.wave_history.pop(0)

        # 更新波形线
        if len(self.time_history) > 1:
            self.wave_line.set_data(self.time_history, self.wave_history)
            self.wave_line.set_color(emotion_color)
            self.wave_line.set_label(f'{self.current_emotion} Wave')

            # 更新填充区域 - 清空旧的collection对象
            for coll in list(self.ax_wave.collections):
                coll.remove()
            self.ax_wave.fill_between(self.time_history, self.wave_history,
                                      color=emotion_color, alpha=0.2)

        # 更新当前点
        self.current_point.set_data([current_time], [wave])
        self.current_point.set_color(emotion_color)

        # 更新标题
        self.wave_title.set_text(f'BREATH WAVEFORM - {self.current_emotion}')
        self.wave_title.set_color(emotion_color)

        # 更新图例
        self.ax_wave.legend(loc='upper right',
                            framealpha=0.7,
                            facecolor=self.colors['background'])

        # 动态调整x轴范围
        if self.time_history:
            x_min = max(0, current_time - 10)
            x_max = max(10, current_time + 1)
            self.ax_wave.set_xlim(x_min, x_max)

    def update_surface_display(self, current_time, current_color):
        """更新3D表面显示"""
        emotion_color = current_color

        # 更新表面数据
        x = np.linspace(0, 2 * np.pi, 50)
        y = np.linspace(0, 1, 20)
        X, Y = np.meshgrid(x, y)

        # 添加时间变化的动态效果
        Z = np.sin(X + current_time * 0.5) * Y * (0.8 + 0.2 * np.sin(current_time))

        # 清除旧表面
        self.ax_surface.clear()

        # 使用情绪颜色相关的colormap
        # 需要将 rgb tuple 转为 hex 或者直接用 segmentdata
        # Matplotlib LinearSegmentedColormap 接受 color list
        cmap = LinearSegmentedColormap.from_list(
            'emotion_cmap', ['#0A0E17', emotion_color, '#FFFFFF']
        )

        # 创建新表面
        surf = self.ax_surface.plot_surface(
            X, Y, Z,
            cmap=cmap,
            alpha=0.8,
            linewidth=0.1,
            antialiased=True
        )

        # 恢复视图设置
        self.ax_surface.view_init(elev=30, azim=45 + current_time * 10)
        self.ax_surface.set_xlabel('Phase', fontsize=9, color=self.colors['text'])
        self.ax_surface.set_ylabel('Amplitude', fontsize=9, color=self.colors['text'])
        self.ax_surface.set_zlabel('Value', fontsize=9, color=self.colors['text'])

        # 更新标题
        self.surface_title = self.ax_surface.set_title(f'3D WAVE SURFACE - {self.current_emotion}',
                                                       fontsize=14,
                                                       color=emotion_color,
                                                       fontweight='bold',
                                                       pad=20)

        # 添加颜色条（只添加一次）
        if not hasattr(self, 'colorbar_added'):
            self.fig.colorbar(surf, ax=self.ax_surface, shrink=0.5, aspect=10)
            self.colorbar_added = True

    def update_params_display(self, wave, angle, current_time, current_color):
        """更新参数面板显示"""
        emotion_color = current_color
        
        # 呼吸周期和范围显示当前插值后的值，更加平滑
        status_values = [
            self.current_emotion,
            f"{self.cycle_duration:.1f} s",
            f"{int(self.servo_min)}° - {int(self.servo_max)}°", # 转int显示
            str(self.breath_count),
            f"{self.current_phase * 100:.1f}%",
            f"{angle:.1f}°",
            f"{60 / self.cycle_duration:.1f} BPM",
        ]

        # 更新每个状态文本
        for i, (text_obj, value) in enumerate(zip(self.status_texts, status_values)):
            text_obj.set_text(value)
            # 情绪文本使用情绪颜色
            if i == 0:
                text_obj.set_color(emotion_color)

        # 更新标题
        self.params_title.set_text(f'STATUS PANEL - {self.current_emotion}')
        self.params_title.set_color(emotion_color)

        # 更新面板边框颜色
        if self.panel_bg is not None:
            self.panel_bg.set_edgecolor(emotion_color)

        # 更新情绪颜色指示器
        self.emotion_color_indicator.set_facecolor(emotion_color)

        # 更新呼吸阶段指示器
        # phase 0-0.5 is effectively inhaling in a sin wave context if we map it right 
        # But here phase 0-1. sin(phase * 2pi). 0-0.5 is positive sin (inhale), 0.5-1 is negative (exhale)
        is_inhaling = math.sin(self.current_phase * 2 * math.pi) > 0
        breath_color = emotion_color if is_inhaling else self.colors['primary']
        self.phase_indicator.set_facecolor(breath_color)

        # 更新呼吸阶段文本
        phase_text = "INHALING" if is_inhaling else "EXHALING"
        self.breath_phase_text.set_text(phase_text)
        self.breath_phase_text.set_color(breath_color)

        # 更新进度条
        self.progress_fg.set_width(0.5 * self.current_phase)
        self.progress_fg.set_facecolor(emotion_color)

        # 进度条颜色渐变
        progress_color = self.interpolate_color(
            self.colors['primary'],
            emotion_color,
            self.current_phase
        )
        self.progress_fg.set_facecolor(progress_color)



    def update_history_display(self, angle, current_color):
        """更新历史图表显示 (支持多色轨迹)"""
        # 更新历史数据
        self.angle_history.append((angle, current_color))
        if len(self.angle_history) > self.max_history:
            self.angle_history.pop(0)

        self.ax_history.clear()
        self.ax_history.set_facecolor(self.colors['panel'])
        self.ax_history.grid(True, alpha=0.2, linestyle=':', color=self.colors['subtext'])
        
        # 设置标签和标题
        self.ax_history.set_xlabel('Time Points', fontsize=11, color=self.colors['text'])
        self.ax_history.set_ylabel('Servo Angle (°)', fontsize=11, color=self.colors['text'])
        self.history_title = self.ax_history.set_title(f'ANGLE HISTORY - {self.current_emotion}',
                                                       fontsize=14,
                                                       color=current_color,
                                                       fontweight='bold',
                                                       pad=15)

        if len(self.angle_history) > 1:
            # 准备 LineCollection 数据
            points = np.array([list(range(len(self.angle_history))), [p[0] for p in self.angle_history]]).T.reshape(-1, 1, 2)
            segments = np.concatenate([points[:-1], points[1:]], axis=1)
            
            # 颜色数组
            colors = [p[1] for p in self.angle_history[:-1]]
            
            lc = LineCollection(segments, colors=colors, linewidth=2, alpha=0.9)
            self.ax_history.add_collection(lc)
            
            # 设置范围
            self.ax_history.set_xlim(0, self.max_history)
            
            angles = [p[0] for p in self.angle_history]
            min_angle = min(angles) - 5
            max_angle = max(angles) + 5
            self.ax_history.set_ylim(min_angle, max_angle)
            
            # 添加参考线
            self.ax_history.axhline(y=self.servo_min, color=self.colors['subtext'],
                                    linestyle='--', alpha=0.5, linewidth=1)
            self.ax_history.axhline(y=self.servo_max, color=self.colors['subtext'],
                                    linestyle='--', alpha=0.5, linewidth=1)

    def update_emotion_indicator(self):
        """更新情绪指示器"""
        emotions = ["Calm", "Anxious", "Relaxed", "Excited", "Deep Sleep", "Meditative"]
        x_positions = np.linspace(0, 1, len(emotions))

        # 更新当前情绪标记
        current_idx = emotions.index(self.current_emotion)
        self.current_emotion_marker.set_xdata([x_positions[current_idx]])
        self.current_emotion_marker.set_color(self.emotion_colors[self.current_emotion])

    def interpolate_color(self, color1, color2, t):
        """在两个颜色之间插值"""
        r1, g1, b1 = to_rgba(color1)[:3]
        r2, g2, b2 = to_rgba(color2)[:3]

        r = r1 + (r2 - r1) * t
        g = g1 + (g2 - g1) * t
        b = b1 + (b2 - b1) * t

        return (r, g, b)

    def change_emotion(self, emotion_name):
        """切换情绪状态（这个函数会被键盘事件调用）"""
        print(f"\nChanging emotion to: {emotion_name}")

        # 从持久化存储中获取参数，如果没有则使用默认值并正确格式化
        if emotion_name not in self.emotion_params:
            # 后备机制：从默认参数创建正确格式的存储
            params = self.get_emotional_params(emotion_name)
            self.emotion_params[emotion_name] = {
                "cycle_duration": params["duration"],
                "servo_min": params["min_angle"],
                "servo_max": params["max_angle"]
            }
            
        saved_params = self.emotion_params[emotion_name]

        # 更新当前情绪
        self.current_emotion = emotion_name
        
        # 设置目标值，让 update_visualization 进行平滑过渡
        self.target_cycle_duration = saved_params["cycle_duration"]
        self.target_servo_min = saved_params["servo_min"]
        self.target_servo_max = saved_params["servo_max"]

        # 获取目标颜色
        target_hex = self.emotion_colors[emotion_name]
        self.target_r, self.target_g, self.target_b = to_rgba(target_hex)[:3]

        print(f"  Target Cycle: {self.target_cycle_duration}s")
        print(f"  Target Range: {self.target_servo_min}-{self.target_servo_max}°")
        print(f"  Target Color: {target_hex}")
        print("  (Transitioning smoothly...)")

        # 更新控制台显示 (文字立即更新，颜色会渐变)
        if self.control_text is not None:
            self.control_text.set_text(f"Current: {emotion_name}")
            # self.control_text.set_color(...) # 颜色在 update loop 中更新

    def immediate_visual_update(self, emotion_color):
        """立即更新可视化元素的颜色"""
        # 1. 更新呼吸器官
        self.organ_bg.set_edgecolor(emotion_color)
        self.organ_core.set_facecolor(emotion_color)
        self.inner_ring.set_edgecolor(emotion_color)
        self.outer_ring.set_edgecolor(emotion_color)
        self.organ_title.set_color(emotion_color)
        self.organ_title.set_text(f'BREATHING ORGAN - {self.current_emotion}')

        # 2. 更新波形图
        self.wave_line.set_color(emotion_color)
        self.wave_line.set_label(f'{self.current_emotion} Wave')
        self.current_point.set_color(emotion_color)
        self.wave_title.set_color(emotion_color)
        self.wave_title.set_text(f'BREATH WAVEFORM - {self.current_emotion}')

        # 3. 更新3D表面标题
        if hasattr(self, 'surface_title'):
            self.surface_title.set_color(emotion_color)
            self.surface_title.set_text(f'3D WAVE SURFACE - {self.current_emotion}')

        # 4. 更新参数面板
        self.params_title.set_color(emotion_color)
        self.params_title.set_text(f'STATUS PANEL - {self.current_emotion}')
        if self.panel_bg is not None:
            self.panel_bg.set_edgecolor(emotion_color)
        self.emotion_color_indicator.set_facecolor(emotion_color)

        # 更新状态文本中的情绪项
        if len(self.status_texts) > 0:
            self.status_texts[0].set_text(self.current_emotion)
            self.status_texts[0].set_color(emotion_color)

        # 5. 更新历史图表
        self.history_line.set_color(emotion_color)
        self.history_line.set_label(f'{self.current_emotion} History')
        self.history_title.set_color(emotion_color)
        self.history_title.set_text(f'ANGLE HISTORY - {self.current_emotion}')

        # 6. 更新全局边框
        if self.border is not None:
            self.border.set_edgecolor(emotion_color)

        # 7. 更新情绪指示器
        self.update_emotion_indicator()

        # 强制重绘
        self.fig.canvas.draw_idle()

    def on_key_press(self, event):
        """处理键盘事件"""
        if event.key == ' ':
            # 空格键暂停/继续
            self.running = not self.running
            status = "PAUSED" if not self.running else "RUNNING"
            print(f"\nSimulation {status}")

        elif event.key == 'r':
            # R键重置
            self.time_history = []
            self.angle_history = [] # Reset history
            self.wave_history = []
            self.phase_history = []
            self.start_time = time.time()
            self.breath_count = 0
            print("\nSimulation Reset")

        elif event.key == '+':
            # 加速
            self.cycle_duration = max(1.0, self.cycle_duration * 0.9)
            self.target_cycle_duration = self.cycle_duration # 更新目标值避免回弹
            self.emotion_params[self.current_emotion]["cycle_duration"] = self.cycle_duration # 保存状态
            print(f"\nSpeed: {self.cycle_duration:.2f}s cycle")

        elif event.key == '-':
            # 减速
            self.cycle_duration = min(15.0, self.cycle_duration * 1.1)
            self.target_cycle_duration = self.cycle_duration
            self.emotion_params[self.current_emotion]["cycle_duration"] = self.cycle_duration 
            print(f"\nSpeed: {self.cycle_duration:.2f}s cycle")

        elif event.key == 'up':
            # 增加最大角度
            self.servo_max = min(180, self.servo_max + 5)
            self.target_servo_max = self.servo_max
            self.emotion_params[self.current_emotion]["servo_max"] = self.servo_max
            print(f"\nMax angle: {self.servo_max}°")

        elif event.key == 'down':
            # 减小最小角度
            self.servo_min = max(0, self.servo_min - 5)
            self.target_servo_min = self.servo_min
            self.emotion_params[self.current_emotion]["servo_min"] = self.servo_min
            print(f"\nMin angle: {self.servo_min}°")

        elif event.key in ['1', '2', '3', '4', '5', '6']:
            # 数字键选择情绪预设
            emotions = {
                '1': "Calm",
                '2': "Anxious",
                '3': "Relaxed",
                '4': "Excited",
                '5': "Deep Sleep",
                '6': "Meditative"
            }

            if event.key in emotions:
                self.change_emotion(emotions[event.key])

        elif event.key == 'c':
            # 切换3D视图
            current_azim = self.ax_surface.azim
            self.ax_surface.view_init(elev=30, azim=current_azim + 90)
            print("\n3D View Rotated")

    def run(self):
        """运行可视化"""
        print("=" * 70)
        print("ENHANCED SENTIENT BREATH VISUALIZATION")
        print("=" * 70)
        print("\nControls:")
        print("  Space: Pause/Resume simulation")
        print("  R: Reset simulation")
        print("  +/-: Change breathing speed")
        print("  ↑/↓: Adjust angle range")
        print("  1-6: Emotion presets (立即切换可视化)")
        print("    1: Calm (4.0s) - 青色")
        print("    2: Anxious (2.0s) - 红色")
        print("    3: Relaxed (6.0s) - 浅绿")
        print("    4: Excited (1.5s) - 黄色")
        print("    5: Deep Sleep (8.0s) - 紫色")
        print("    6: Meditative (10.0s) - 淡紫")
        print("  C: Rotate 3D view")
        print("=" * 70)
        print(f"\nStarting with: {self.current_emotion} mode")
        print(f"Cycle: {self.cycle_duration}s, Range: {self.servo_min}-{self.servo_max}°")
        print("Press 1-6 to change emotion and see immediate visual feedback!")

        # 连接键盘事件
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)

        # 启动动画
        self.animation = FuncAnimation(self.fig, self.update_visualization,
                                       interval=int(self.smoothness * 1000),
                                       blit=False,
                                       cache_frame_data=False)

        # 调整布局
        plt.tight_layout()

        # 显示窗口
        plt.show()


if __name__ == "__main__":
    # 创建可视化实例
    visualizer = EnhancedSentientBreath()

    # 运行
    visualizer.run()