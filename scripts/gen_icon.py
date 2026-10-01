"""生成 Lid 应用图标底稿(1024x1024,供 `tauri icon` 使用)。

macOS Big Sur+ 图标规范:内容(圆角矩形)只占画布约 80%,四周留透明边距;
若内容铺满画布,Dock 会给图标垫一块白色底板(白边问题),务必保留边距。
"""
from PIL import Image, ImageDraw, ImageChops, ImageFilter

S = 2048  # 2x 超采样后缩到 1024
MARGIN = int(S * 0.1)  # 四周透明边距,内容区占 80%
R = S - MARGIN * 2  # 内容区边长
out = "/Users/xiaov/gitmy/lid/app-icon.png"

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

# 垂直渐变背景:靛蓝 -> 紫
top, bottom = (72, 66, 224), (124, 58, 237)
bg = Image.new("RGBA", (S, S))
d = ImageDraw.Draw(bg)
for y in range(MARGIN, S - MARGIN):
    t = (y - MARGIN) / (R - 1)
    c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)) + (255,)
    d.line([(MARGIN, y), (S - MARGIN, y)], fill=c)

# 圆角矩形蒙版(macOS 图标比例,仅覆盖内容区)
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle(
    [MARGIN, MARGIN, S - MARGIN - 1, S - MARGIN - 1], radius=int(R * 0.22), fill=255
)
img = ImageChops.composite(bg, img, mask)

# 太阳:实心核心圆 + 8 条圆头放射光线(极简几何风,呼应"保持唤醒")
# 光线用"圆角矩形旋转"绘制,避免 line+圆叠加产生的接缝
cx, cy = S // 2, S // 2  # 内容区中心
CR = R / 2  # 内容区半径
r_core = int(CR * 0.28)  # 核心圆半径
r1, r2 = int(CR * 0.43), int(CR * 0.65)  # 光线内/外端
w = int(CR * 0.085)  # 光线粗细(圆头)

sd = ImageDraw.Draw(img)
# 核心圆
sd.ellipse([cx - r_core, cy - r_core, cx + r_core, cy + r_core], fill=(255, 255, 255, 255))

# 光线:竖直胶囊旋转 8 个角度
import math

len_ray = r2 - r1
cap = Image.new("RGBA", (w, len_ray), (0, 0, 0, 0))
ImageDraw.Draw(cap).rounded_rectangle(
    [0, 0, w - 1, len_ray - 1], radius=w // 2, fill=(255, 255, 255, 255)
)
mid_r = (r1 + r2) / 2
for i in range(8):
    ang = i * 45 - 90  # 数学角,-90 从正上方开始
    mx = cx + math.cos(math.radians(ang)) * mid_r
    my = cy + math.sin(math.radians(ang)) * mid_r
    ray = cap.rotate(i * 45, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(ray, (int(mx - ray.width / 2), int(my - ray.height / 2)))

img = img.resize((1024, 1024), Image.LANCZOS)
img.save(out)
print("saved:", out, img.size)
