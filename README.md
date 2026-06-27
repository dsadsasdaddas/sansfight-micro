# SansFight micro —— T-Dongle S3 上的 SansFight 迷你版

把 [SansFight](#)（Undertale「Sans 战斗」同人游戏）的核心**「红心躲骨」**做成一块 **LILYGO T-Dongle S3**（ESP32-S3 + 0.96" 160×80 屏 + 1 个按钮）上的一键小游戏，用 **CircuitPython** 实现。

> ⚠️ 这**不是**原版 SansFight 的移植。原版是 C++/SDL2/OpenGL 桌面游戏（640×480、54MB 资源、24 回合弹幕），ESP32 没有 GPU、只有 ~320KB 可用 RAM，**根本跑不动**。这里是借原版的核心玩法和手感，从零在 160×80 小屏上重写的一个迷你版。详见下文「为什么不是完整版」。

---

## 玩法（一个按钮）

- **按住按钮** → 红心**上升**；**松开** → 红心**下落**（重力）。不用狂点，按住/松开控制高度。
- 白色**骨墙**从右边滚过来，中间有个**缝隙**——让红心穿过缝隙，别碰到骨头。
- 每穿一堵墙 **+1 分**；撞骨头 **-1 命**，共 **3 命**（被撞后短暂无敌闪烁）。
- 3 命用完 → `OVER 分数`，再按一下重新开始。墙会越来越快。

---

## 硬件

| 物品 | 说明 |
|---|---|
| LILYGO T-Dongle S3 | ESP32-S3，自带 0.96" ST7735 屏（80×160），1 个按钮（GPIO0），16MB Flash |
| USB-C 数据线 | 供电 + 烧录（要数据线，不是纯充电线） |

屏引脚（与 CircuitPython 官方 `lilygo_tdongle_s3` 板型一致）：

| 信号 | GPIO |
|---|---|
| MOSI / SCK / DC / CS / RST | 3 / 5 / 2 / 4 / 1 |
| 背光 BL | **38** |
| 按钮 | 0 |

---

## 🔑 关键坑：背光是「低电平有效」

**这是整个项目最容易栽的坑，重点写一下。**

T-Dongle S3 的屏背光是 **低电平有效（active-low）**。也就是说：

- 在 CircuitPython 里，**必须 `display.brightness = 0` 才能点亮屏**（默认是灭的！）。
- 我一开始用 LovyanGFX（C++/Arduino）写，把背光脚按 **高电平** 驱动（`setBrightness(255)` / `digitalWrite(38, HIGH)`）——对 active-low 来说 HIGH = **关**——结果屏死活不亮，黑屏排查了十几轮才在 [xuemate-dongle](https://github.com/dsadsasdaddas/xuemate-dongle) 的 README 里找到这句：

> 屏幕一片黑 — T-Dongle S3 背光低电平有效，`code.py` 里已设 `display.brightness = 0` 点亮。

所以本仓库的 `code.py` 第一行有效代码就是：

```python
display = board.DISPLAY
display.brightness = 0   # ← 背光低电平有效，0 才亮
```

**如果哪天你换 LovyanGFX / TFT_eSPI 之类 C++ 库写这块屏**，记得把背光脚设成 **低电平点亮**（或反转 PWM），否则就是黑屏。

---

## 烧录 / 安装

### 1. 给板子刷 CircuitPython（一次性）

板子出厂带 LILYGO UF2 引导器，最省事的刷法：

1. **按住板子上的 BOOT 键**，插入 USB → 出现一个名为 **`LILYGOBOOT`** 的 U 盘
2. 去 [circuitpython.org/board/lilygo_tdongle_s3](https://circuitpython.org/board/lilygo_tdongle_s3) 下载 `.uf2` 固件
3. 把 `.uf2` 拖进那个 U 盘，板子自动重启，变成一个名为 **CIRCUITPY** 的 U 盘

> 也可以用 esptool 刷（下载 `.bin`，`esptool --port COMx write_flash 0x0 xxx.bin`），但 UF2 方式最稳，不用跟 BOOT 键较劲。

### 2. 放入游戏

把本仓库的 [`code.py`](code.py) 复制到 CIRCUITPY 盘根目录（覆盖默认的 `Hello World!`）。CircuitPython 检测到文件变化会**自动重载**，立刻运行。

> `code.py` 只用到 CircuitPython 自带模块（`displayio` / `terminalio` / `digitalio`）+ `adafruit_display_text`。如果报缺库，在 CIRCUITPY 盘里装一下：`circup install adafruit_display_text`。

### 3. 看屏幕

插上电，屏幕亮起 → 出现 `SansFight` 标题 + 一个上下飘的红心（菜单）。**按住按钮**开始游戏。

---

## 文件

```
code.py      游戏主程序（CircuitPython，~5KB，零外部素材，全部程序化绘制）
README.md    本文档
```

---

## 为什么不是完整版 SansFight

原版 SansFight 的硬伤（对 ESP32 而言）：

| # | 问题 | 细节 |
|---|---|---|
| 1 | 没 GPU / OpenGL | 整个渲染层是 GLSL 着色器 + VAO/VBO + FBO Canvas，ESP32 没有 |
| 2 | 内存 | 原版满项目 `shared_ptr` + `variant` + 字形图集 + 音频 PCM，ESP32 只有 ~320KB 可用 RAM、无 PSRAM |
| 3 | 资源 | 54MB > 16MB Flash，装不下 |
| 4 | 算力 | 单回合 190 个冲击波 + 44 列正弦骨 + 30dmg/s 碰撞，240MHz 软件渲染撑不住 |
| 5 | 输入 | 原版要方向键 + Z + X，T-Dongle 只有 1 个按钮 |

所以本迷你版只取核心「红心 + 重力 + 骨缝躲避」这一条玩法线，重写成一键小屏游戏。

---

## 改手感 / 扩展

`code.py` 顶部的常数随便调：

```python
GAP_H = 30        # 骨缝大小，越大越简单
GRAVITY = 200.0   # 下落重力
THRUST = 480.0    # 按住时的上升推力
MAX_VY = 110.0    # 最大升降速度
SPAWN_GAP = 72    # 骨墙间距
```

想加更「SansFight」的味：蓝色骨头（停下才安全）、受击红屏、像素 Sans 脸…… 都在这个框架里加就行。

## License

MIT
