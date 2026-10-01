"""给 README 截图补圆角:把窗口圆角弧外的桌面/壁纸残影裁成透明。

真实截图是方形画布,而 macOS 窗口是圆角的,四角弧外会混进桌面壁纸。
本脚本按窗口实际圆角生成抗锯齿圆形蒙版(4x 超采样),就地覆盖原图。

蒙版半径比窗口实测圆角(约 26px@2x)略收 2px:窗口自带 2px 边缘高亮,
收边可以让蒙版边界落在高亮条内,避免壁纸与高亮之间的过渡光晕残留。

用法:python3 scripts/round_screenshot.py [文件...]
不传参数则处理 docs/ss*.png;就地覆盖(git 中有原始版本可回退)。
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SS = 4  # 蒙版超采样倍数,保证圆弧边缘抗锯齿
RADIUS = 24  # 蒙版圆角半径(2x 像素),比窗口实际圆角略小,向内收边


def round_corners(path: Path) -> None:
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    mask = Image.new("L", (w * SS, h * SS), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, w * SS - 1, h * SS - 1], radius=RADIUS * SS, fill=255
    )
    mask = mask.resize((w, h), Image.LANCZOS)
    im.putalpha(mask)
    im.save(path)
    print("rounded:", path)


def main() -> None:
    files = [Path(a) for a in sys.argv[1:]] or sorted((ROOT / "docs").glob("ss*.png"))
    for f in files:
        round_corners(f)


if __name__ == "__main__":
    main()
