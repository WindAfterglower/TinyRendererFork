import struct
import tkinter as tk
from pathlib import Path
import  pathlib;

# ----------------- TGA 读取部分（支持灰度、真彩色、RLE 压缩） -----------------
def read_tga(filepath):
    with open(filepath, 'rb') as f:
        header = f.read(18)
        id_length = header[0]
        colormap_type = header[1]
        image_type = header[2]

        # 支持未压缩真彩色(2)、RLE真彩色(10)、未压缩灰度(3)、RLE灰度(11)
        if colormap_type != 0:
            raise ValueError("Colormapped TGA not supported")
        if image_type not in (2, 3, 10, 11):
            raise ValueError(f"Unsupported image type: {image_type}")

        width = struct.unpack_from('<H', header, 12)[0]
        height = struct.unpack_from('<H', header, 14)[0]
        bpp = header[16]
        descriptor = header[17]

        f.read(id_length)  # 跳过图像 ID

        # 读取像素数据
        if image_type in (2, 3):   # 未压缩
            bytes_per_pixel = bpp // 8
            raw_data = f.read(width * height * bytes_per_pixel)
        else:                      # RLE 压缩
            raw_data = decode_tga_rle(f, width, height, bpp)

        # 转换 BGR / 灰度 -> RGB
        rgb_data = convert_to_rgb(raw_data, bpp)

        # 上下翻转（若原点在左下角）
        if not (descriptor & 0x20):
            rgb_data = flip_vertically(rgb_data, width, height)

        return width, height, rgb_data

def decode_tga_rle(stream, width, height, bpp):
    bytes_per_pixel = bpp // 8
    total_bytes = width * height * bytes_per_pixel
    output = bytearray()

    while len(output) < total_bytes:
        packet_header = stream.read(1)[0]
        count = (packet_header & 0x7F) + 1
        if packet_header & 0x80:  # RLE 包
            pixel = stream.read(bytes_per_pixel)
            output.extend(pixel * count)
        else:                     # 原始包
            output.extend(stream.read(count * bytes_per_pixel))

    return bytes(output)

def convert_to_rgb(data, bpp):
    rgb = bytearray()
    if bpp == 8:  # 灰度图
        for gray in data:
            rgb.extend([gray, gray, gray])
    elif bpp == 24:
        for i in range(0, len(data), 3):
            b, g, r = data[i], data[i+1], data[i+2]
            rgb.extend([r, g, b])
    elif bpp == 32:
        for i in range(0, len(data), 4):
            b, g, r, a = data[i], data[i+1], data[i+2], data[i+3]
            rgb.extend([r, g, b])  # 忽略 Alpha
    else:
        raise ValueError(f"Unsupported bpp: {bpp}")
    return bytes(rgb)

def flip_vertically(rgb_data, width, height):
    row_size = width * 3
    flipped = bytearray()
    for y in range(height - 1, -1, -1):
        start = y * row_size
        flipped.extend(rgb_data[start:start + row_size])
    return bytes(flipped)

# ----------------- 图像缩放（最近邻插值） -----------------
def resize_nearest(rgb_bytes, orig_w, orig_h, new_w, new_h):
    """最近邻插值缩放，返回新图像的 RGB 字节流"""
    row_size = orig_w * 3
    output = bytearray()
    for y in range(new_h):
        src_y = min(int(y * orig_h / new_h), orig_h - 1)
        row_start = src_y * row_size
        for x in range(new_w):
            src_x = min(int(x * orig_w / new_w), orig_w - 1)
            src_idx = row_start + src_x * 3
            output.extend(rgb_bytes[src_idx:src_idx + 3])
    return bytes(output)

# ----------------- 带缩放的查看器 GUI -----------------
def show_tga(filepath):
    w, h, rgb_bytes = read_tga(filepath)

    # 保存原始数据，用于后续缩放
    orig_w, orig_h = w, h
    orig_rgb = rgb_bytes

    root = tk.Tk()
    root.title(f"TGA Viewer - {Path(filepath).name}")
    root.geometry("800x600")  # 初始窗口大小

    # 滚动条区域
    frame = tk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(frame, bg='gray')
    hbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL, command=canvas.xview)
    vbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
    canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

    hbar.pack(side=tk.BOTTOM, fill=tk.X)
    vbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # 初始显示原始大小
    ppm = f'P6\n{orig_w} {orig_h}\n255\n'.encode('ascii') + orig_rgb
    photo = tk.PhotoImage(data=ppm)
    img_on_canvas = canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    canvas.config(scrollregion=canvas.bbox(tk.ALL))

    # 当前缩放因子
    scale = 1.0

    def update_scale(new_scale):
        nonlocal scale, photo
        scale = new_scale
        new_w = max(1, int(orig_w * scale))
        new_h = max(1, int(orig_h * scale))
        # 重新缩放图像
        scaled_data = resize_nearest(orig_rgb, orig_w, orig_h, new_w, new_h)
        ppm_new = f'P6\n{new_w} {new_h}\n255\n'.encode('ascii') + scaled_data
        photo = tk.PhotoImage(data=ppm_new)
        canvas.itemconfig(img_on_canvas, image=photo)
        canvas.config(scrollregion=canvas.bbox(tk.ALL))

    # ---- 鼠标滚轮事件（跨平台） ----
    def on_mousewheel(event):
        """Windows / macOS 滚轮"""
        if event.delta > 0:
            new_scale = scale * 1.1
        else:
            new_scale = scale / 1.1
        new_scale = max(0.1, min(10.0, new_scale))  # 限制缩放范围
        update_scale(new_scale)

    def on_scroll_up(event):
        """Linux 向上滚动（Button-4）"""
        new_scale = scale * 1.1
        new_scale = min(10.0, new_scale)
        update_scale(new_scale)

    def on_scroll_down(event):
        """Linux 向下滚动（Button-5）"""
        new_scale = scale / 1.1
        new_scale = max(0.1, new_scale)
        update_scale(new_scale)

    # 绑定到 Canvas 和顶层窗口，确保鼠标在图片上时也能缩放
    for widget in (canvas, root):
        widget.bind("<MouseWheel>", on_mousewheel)         # Windows/Mac
        widget.bind("<Button-4>", on_scroll_up)            # Linux 上滚
        widget.bind("<Button-5>", on_scroll_down)          # Linux 下滚

    root.mainloop()

if __name__ == "__main__":
    # 改成你的 TGA 文件路径
    
    tga_path =  str(pathlib.Path(__file__).parent) + "\\framebuffer.tga"
    show_tga(tga_path)