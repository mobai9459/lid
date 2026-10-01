"""生成 LidSwitch 应用图标底稿（1024x1024，供 `tauri icon` 使用）"""
from PIL import Image, ImageDraw, ImageChops, ImageFilter

S = 2048  # 2x 超采样后缩到 1024
out = "/Users/xiaov/gitmy/pudong/lid-switch/app-icon.png"

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

# 垂直渐变背景：靛蓝 -> 紫
top, bottom = (72, 66, 224), (124, 58, 237)
bg = Image.new("RGBA", (S, S))
d = ImageDraw.Draw(bg)
for y in range(S):
    t = y / (S - 1)
    c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)) + (255,)
    d.line([(0, y), (S, y)], fill=c)

# 圆角矩形蒙版（macOS 图标比例）
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.22), fill=255)
img = ImageChops.composite(bg, img, mask)

# 新月：大圆减去偏移圆（S=2048 坐标系，居中构图，开口朝右上）
moon = Image.new("L", (S, S), 0)
m = ImageDraw.Draw(moon)
m.ellipse([1024 - 620, 1024 - 620, 1024 + 620, 1024 + 620], fill=255)
m.ellipse([1336 - 516, 808 - 516, 1336 + 516, 808 + 516], fill=0)
moon = moon.filter(ImageFilter.GaussianBlur(3))
img.paste(Image.new("RGBA", (S, S), (255, 255, 255, 255)), (0, 0), moon)

# 小星星（远离月亮主体）
sd = ImageDraw.Draw(img)
for x, y, r, a in [(1500, 400, 30, 225), (600, 1600, 24, 195)]:
    sd.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, a))

img = img.resize((1024, 1024), Image.LANCZOS)
img.save(out)
print("saved:", out, img.size)
