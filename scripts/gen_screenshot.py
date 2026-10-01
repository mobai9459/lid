"""生成 README 用的应用截图。

原理:screencapture 需要屏幕录制权限(终端环境通常没有),所以用
Chrome headless 渲染真实 UI 代码(注入 Tauri mock),再合成 macOS
窗口样式(标题栏 + 红绿灯 + 圆角 + 阴影),输出 docs/screenshot.png。

用法:python3 scripts/gen_screenshot.py
依赖:Pillow、本机 Chrome。
"""
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
UI = ROOT / "ui"
OUT = ROOT / "docs" / "screenshot.png"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SF_FONT = "/System/Library/Fonts/SFNS.ttf"

MOCK_INVOKE = """
window.__TAURI__ = {
  core: {
    invoke: async (cmd) => {
      if (cmd === "get_lid_sleep_status") return false;
      if (cmd === "has_cached_auth") return false;
      return undefined;
    },
  },
};
"""

MOCK_HTML = """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <title>Lid</title>
    <link rel="stylesheet" href="{css}" />
    <script>{mock}</script>
  </head>
  <body>
    <main class="card">
      <div class="row">
        <div class="text">
          <div class="title" id="t-title"></div>
          <div class="subtitle" id="t-subtitle"></div>
        </div>
        <button id="switch" class="switch" role="switch" aria-checked="false" aria-label="Lid"></button>
      </div>
      <div id="status" class="status"></div>
      <div id="auth-layer" class="auth-layer hidden">
        <div class="auth-title" id="t-auth-title"></div>
        <div class="auth-row">
          <input id="auth-pass" type="password" autocomplete="off" />
          <button id="auth-ok" class="auth-btn primary"></button>
          <button id="auth-cancel" class="auth-btn"></button>
        </div>
        <div id="auth-error" class="auth-error"></div>
      </div>
    </main>
    <script src="{js}"></script>
  </body>
</html>
"""


def render_content(workdir: Path) -> Image.Image:
    html = MOCK_HTML.format(css=UI / "style.css", js=UI / "main.js", mock=MOCK_INVOKE)
    page = workdir / "index.html"
    shot = workdir / "content.png"
    page.write_text(html)
    subprocess.run(
        [
            CHROME,
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            "--lang=zh-CN",
            "--window-size=420,180",
            f"--screenshot={shot}",
            f"file://{page}",
        ],
        check=True,
        capture_output=True,
    )
    return Image.open(shot).convert("RGBA")


def compose(content: Image.Image) -> Image.Image:
    title_h, radius = 28, 10
    win_w, win_h = content.width, content.height + title_h

    window = Image.new("RGBA", (win_w, win_h), (0, 0, 0, 0))
    mask = Image.new("L", (win_w, win_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, win_w - 1, win_h - 1], radius=radius, fill=255)
    window.paste(Image.new("RGBA", (win_w, win_h), (30, 30, 32, 255)), (0, 0), mask)

    d = ImageDraw.Draw(window)
    d.line([(radius, title_h), (win_w - radius, title_h)], fill=(255, 255, 255, 20), width=1)
    # 红绿灯
    for i, color in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        cx = 20 + i * 20
        d.ellipse([cx - 6, title_h // 2 - 6, cx + 6, title_h // 2 + 6], fill=color)
    # 居中标题
    font = ImageFont.truetype(SF_FONT, 13)
    bbox = d.textbbox((0, 0), "Lid", font=font)
    d.text(
        ((win_w - bbox[2] + bbox[0]) // 2, (title_h - bbox[3] + bbox[1]) // 2 - bbox[1] + 1),
        "Lid",
        font=font,
        fill=(245, 245, 247, 255),
    )
    window.paste(content, (0, title_h), mask.crop((0, title_h, win_w, win_h)))

    # 画布 + 投影
    pad_x, pad_top, pad_bottom = 60, 30, 50
    canvas = Image.new("RGBA", (win_w + pad_x * 2, win_h + pad_top + pad_bottom), (0, 0, 0, 0))
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [pad_x, pad_top, pad_x + win_w - 1, pad_top + win_h - 1],
        radius=radius,
        fill=(0, 0, 0, 110),
    )
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)))
    canvas.alpha_composite(window, (pad_x, pad_top))
    return canvas


def main():
    OUT.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        content = render_content(Path(tmp))
    compose(content).save(OUT)
    print("saved:", OUT)


if __name__ == "__main__":
    main()
