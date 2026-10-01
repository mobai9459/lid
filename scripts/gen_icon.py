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

# 新月:大圆减去偏移圆(开口朝右上),尺寸按内容区等比缩放
cx, cy = S // 2, S // 2  # 内容区中心
mr = int(620 * 0.8)  # 月亮大圆半径
ox, oy, orr = int(312 * 0.8), int(-216 * 0.8), int(516 * 0.8)  # 减圆偏移与半径
moon = Image.new("L", (S, S), 0)
m = ImageDraw.Draw(moon)
m.ellipse([cx - mr, cy - mr, cx + mr, cy + mr], fill=255)
m.ellipse([cx + ox - orr, cy + oy - orr, cx + ox + orr, cy + oy + orr], fill=0)
moon = moon.filter(ImageFilter.GaussianBlur(2))
img.paste(Image.new("RGBA", (S, S), (255, 255, 255, 255)), (0, 0), moon)

# 小星星(远离月亮主体,单颗)
sd = ImageDraw.Draw(img)
sx, sy, r, a = MARGIN + int((380 - MARGIN) * 0.8), MARGIN + int((1600 - MARGIN) * 0.8), 19, 195
sd.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 255, 255, a))

img = img.resize((1024, 1024), Image.LANCZOS)
img.save(out)
print("saved:", out, img.size)
