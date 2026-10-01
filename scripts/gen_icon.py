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

# 夜空主题:左下弯月 + 右上小星(呼应"合盖/睡眠"场景)
import math

cx, cy = S // 2, S // 2  # 内容区中心
CR = R / 2  # 内容区半径
C2 = 0.7071  # sin45 = cos45

# --- 弯月:大圆减去朝右上 45° 偏移的"咬"圆,月角指向星星;月亮为画面主体 ---
mR = int(CR * 0.60)  # 月亮半径
mx = cx - int(R * 0.10)
my = cy + int(R * 0.10)
bR = int(mR * 0.82)  # 咬圆半径
bd = int(mR * 0.55)  # 咬圆圆心偏移距离
bx, by = mx + int(bd * C2), my - int(bd * C2)

moon_mask = Image.new("L", (S, S), 0)
md = ImageDraw.Draw(moon_mask)
md.ellipse([mx - mR, my - mR, mx + mR, my + mR], fill=255)
md.ellipse([bx - bR, by - bR, bx + bR, by + bR], fill=0)
white = Image.new("RGBA", (S, S), (255, 255, 255, 255))
img = Image.composite(white, img, moon_mask)

# --- 星芒:四角星,内凹比 0.3;独立小图 4x 超采样后贴回,保证尖角平滑;仅作右上角点缀 ---
sR = int(CR * 0.075)  # 星星外接半径
sx = cx + int(R * 0.30)
sy = cy - int(R * 0.30)
inr = 0.30  # 内凹半径比例

ss = 4
tile = ss * (2 * sR + 8)  # 星星画布,外留余量
stim = Image.new("RGBA", (tile, tile), (0, 0, 0, 0))
pts = []
for k in range(4):
    ao = math.radians(k * 90 - 90)  # 外点:上、右、下、左
    ai = math.radians(k * 90 - 45)  # 内点:斜向
    pts.append((tile / 2 + sR * ss * math.cos(ao), tile / 2 + sR * ss * math.sin(ao)))
    pts.append(
        (tile / 2 + sR * inr * ss * math.cos(ai), tile / 2 + sR * inr * ss * math.sin(ai))
    )
ImageDraw.Draw(stim).polygon(pts, fill=(255, 255, 255, 255))
stim = stim.resize((tile // ss, tile // ss), Image.LANCZOS)
img.alpha_composite(stim, (sx - tile // ss // 2, sy - tile // ss // 2))

img = img.resize((1024, 1024), Image.LANCZOS)
img.save(out)
print("saved:", out, img.size)
