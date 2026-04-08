import sys
import threading
import pygame
import time
import subprocess
import re


class FrameReader(threading.Thread):
    def __init__(self, program_path, input_file):
        threading.Thread.__init__(self)
        self.frames = []
        self.running = True
        self.program_path = program_path
        self.input_file = input_file

    def run(self):
        # 使用 subprocess 运行外部程序
        process = subprocess.Popen(
            [self.program_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 将输入文件的内容传递给外部程序
        with open(self.input_file, 'r') as f:
            input_data = f.read()
        process.stdin.write(input_data)
        process.stdin.close()

        while self.running:
            line = process.stdout.readline()
            if not line:
                break  # EOF
            line = line.strip()
            if line == "End!":
                break  # 输入结束
            if not line:
                continue
            # 解析帧数据
            try:
                frame = self.parse_frame(line, process.stdout)
                if frame:
                    self.frames.append(frame)
            except Exception as e:
                print(f"Error parsing frame: {e}")
                self.stop()  # 停止读取
                break

        # 等待进程结束
        process.wait()

    def parse_frame(self, first_line, stdout):
        # 第一行：两个整数，表示总的 x 和 y
        width_height = first_line.strip().split()
        if len(width_height) != 2:
            raise ValueError("Invalid width and height format")
        width = int(width_height[0])
        height = int(width_height[1])

        # 第二行：RLE 格式的模式
        rle_pattern = stdout.readline().strip()

        # 最后一行：两个整数，表示 generation 和 live cells
        last_line = stdout.readline().strip()
        if not last_line:
            raise ValueError("Missing generation and live cells info")
        gen_live = last_line.split()
        if len(gen_live) != 2:
            raise ValueError("Invalid generation and live cells format")
        generation = int(gen_live[0])
        live_cell_count = int(gen_live[1])

        # 解析 RLE 格式，获取活细胞的位置
        cell_positions = self.parse_rle(rle_pattern, width, height)

        return {
            'generation': generation,
            'live_cell_count': live_cell_count,
            'width': width,
            'height': height,
            'cells': cell_positions
        }

    def parse_rle(self, rle_pattern, grid_width, grid_height):
        # 解析 RLE 格式的字符串，返回活细胞的位置列表
        # 验证 RLE 格式
        if not rle_pattern.endswith('!'):
            raise ValueError("RLE pattern must end with '!'")

        rle_pattern = rle_pattern[:-1]  # 去掉末尾的 '!'
        tokens = re.findall(r'(\d*)([bo$])', rle_pattern)
        cell_positions = []
        x = 0
        y = 0
        for count_str, symbol in tokens:
            count = int(count_str) if count_str else 1
            if symbol == 'b':  # 空细胞
                x += count
            elif symbol == 'o':  # 活细胞
                for _ in range(count):
                    if x >= grid_width or y >= grid_height:
                        raise ValueError("Pattern exceeds grid dimensions")
                    cell_positions.append((x, y))
                    x += 1
            elif symbol == '$':  # 换行
                y += count
                x = 0
            else:
                raise ValueError(f"Invalid symbol '{symbol}' in RLE pattern")
            if y >= grid_height:
                raise ValueError("Pattern exceeds grid height")
        return cell_positions

    def stop(self):
        self.running = False


def draw_frame(screen, frame, zoom_factor, offset_x, offset_y, boundary_rect, show_grid):
    width = frame['width']
    height = frame['height']
    cells = frame['cells']

    # 计算每个细胞的大小
    cell_size_x = boundary_rect.width / width * zoom_factor
    cell_size_y = boundary_rect.height / height * zoom_factor
    cell_size = min(cell_size_x, cell_size_y)

    # 绘制边界（固定位置和大小）
    pygame.draw.rect(screen, (0, 0, 0), boundary_rect, 1)  # 1像素的边框

    # 创建一个Surface用于裁剪绘制区域
    cell_surface = pygame.Surface((boundary_rect.width, boundary_rect.height))
    cell_surface.fill((255, 255, 255))  # 白色背景

    # 固定的网格线阈值，单位：像素
    grid_threshold = 5  # 单位：像素

    # 计算可见区域在网格坐标系中的范围
    start_x = int((-offset_x) / cell_size) - 2
    end_x = int((boundary_rect.width - offset_x) / cell_size) + 2
    start_y = int((-offset_y) / cell_size) - 2
    end_y = int((boundary_rect.height - offset_y) / cell_size) + 2

    # 当细胞尺寸过小时，进行细胞聚合显示
    if cell_size < 1:
        # 设置最小聚合块尺寸
        min_aggregate_size = 2  # 最小聚合块尺寸（像素）

        # 计算聚合因子
        aggregate_factor = int(1 / cell_size) + 1
        aggregate_size = max(cell_size * aggregate_factor, min_aggregate_size)

        aggregate_start_x = start_x // aggregate_factor
        aggregate_end_x = end_x // aggregate_factor
        aggregate_start_y = start_y // aggregate_factor
        aggregate_end_y = end_y // aggregate_factor

        # 创建一个集合，存储聚合区域内有活细胞的位置
        aggregate_set = set()
        for x_cell, y_cell in cells:
            agg_x = x_cell // aggregate_factor
            agg_y = y_cell // aggregate_factor
            if agg_x >= aggregate_start_x and agg_x <= aggregate_end_x and agg_y >= aggregate_start_y and agg_y <= aggregate_end_y:
                draw_x = (agg_x * aggregate_factor) * cell_size + offset_x
                draw_y = (agg_y * aggregate_factor) * cell_size + offset_y
                rect = pygame.Rect(draw_x, draw_y, aggregate_size, aggregate_size)
                pygame.draw.rect(cell_surface, (0, 0, 0), rect)

    else:
        # 绘制活细胞
        for x_cell, y_cell in cells:
            # 计算细胞在边界内的位置
            draw_x = x_cell * cell_size + offset_x
            draw_y = y_cell * cell_size + offset_y
            rect = pygame.Rect(draw_x, draw_y, cell_size, cell_size)
            pygame.draw.rect(cell_surface, (0, 0, 0), rect)

    # 绘制无限网格线
    if cell_size >= grid_threshold:
        # 垂直线
        for i in range(start_x, end_x):
            x = i * cell_size + offset_x
            pygame.draw.line(cell_surface, (200, 200, 200), (x, 0), (x, boundary_rect.height))
        # 水平线
        for j in range(start_y, end_y):
            y = j * cell_size + offset_y
            pygame.draw.line(cell_surface, (200, 200, 200), (0, y), (boundary_rect.width, y))

    # 将细胞表面绘制到屏幕上
    screen.blit(cell_surface, (boundary_rect.x, boundary_rect.y))


def draw_text(screen, text, x, y, font):
    img = font.render(text, True, (0, 0, 0))
    screen.blit(img, (x, y))


def draw_speed_slider(screen, speed_index, max_speed_index, font):
    # 绘制底部的速度滑块
    slider_width = 200
    slider_height = 20
    screen_width, screen_height = screen.get_size()
    slider_x = (screen_width - slider_width) / 2
    slider_y = screen_height - slider_height - 10
    slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)

    # 绘制滑槽
    pygame.draw.rect(screen, (200, 200, 200), slider_rect)

    # 绘制滑块
    position = (speed_index / max_speed_index) * slider_width
    knob_x = slider_x + position - 5
    knob_y = slider_y - 5
    knob_rect = pygame.Rect(knob_x, knob_y, 10, slider_height + 10)
    pygame.draw.rect(screen, (0, 0, 0), knob_rect)

    # 显示速度文本
    speed_factors = [1 / 32, 1 / 16, 1 / 8, 1 / 4, 1 / 2, 1,
                     2, 4, 8, 16, 32, 64, 128]
    speed_text = f"Speed: {speed_factors[speed_index]}x"
    draw_text(screen, speed_text, slider_x, slider_y - 30, font)

    return slider_rect


def main():
    pygame.init()

    # 获取屏幕大小，设置初始窗口大小为屏幕的80%
    infoObject = pygame.display.Info()
    screen_width = int(infoObject.current_w * 0.8)
    screen_height = int(infoObject.current_h * 0.8)
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
    pygame.display.set_caption("Conway's Game of Life Visualizer")

    # 获取外部程序路径和输入文件路径
    import argparse
    parser = argparse.ArgumentParser(description="Conway's Game of Life Visualizer")
    parser.add_argument('program', help='Path to the external program')
    parser.add_argument('input_file', help='Path to the input file for the external program')
    parser.add_argument('--preload-frames', dest="preload", action="store", type=int, default=0,
                        help='Load frames before running')
    args = parser.parse_args()

    # 启动帧读取线程
    frame_reader = FrameReader(args.program, args.input_file)
    frame_reader.start()

    clock = pygame.time.Clock()

    # 播放速度控制变量
    speed_index = 5  # 初始速度索引对应1x
    speed_factors = [1 / 32, 1 / 16, 1 / 8, 1 / 4, 1 / 2, 1,
                     2, 4, 8, 16, 32, 64, 128]
    speed_multiplier = speed_factors[speed_index]
    max_speed_index = len(speed_factors) - 1

    # 缩放控制变量
    zoom_factor = None  # 初始为 None，后面根据网格大小自动调整
    min_zoom = 0.01
    max_zoom = 100.0

    # 视图偏移量（用于移动）
    offset_x = 0
    offset_y = 0
    dragging = False

    # 播放控制
    paused = False

    # 当前帧索引
    current_frame_index = -1

    # 时间追踪
    last_frame_time = time.time()

    # 定义边界矩形（位置和大小）
    boundary_margin = 50  # 边界与窗口边缘的间距
    slider_height = 70  # 为速度滑块和文本留出的空间
    top_margin = 120  # 为顶部标题和文本留出的空间

    boundary_rect = pygame.Rect(
        boundary_margin,
        top_margin,
        screen_width - 2 * boundary_margin,
        screen_height - top_margin - slider_height - boundary_margin
    )

    # 设置字体（使用 Times New Roman）
    font = pygame.font.SysFont('Times New Roman', 24)
    title_font = pygame.font.SysFont('Times New Roman', 32)

    running = True
    while running:
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                frame_reader.stop()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_UP:
                    # 放大
                    zoom_factor *= 1.1
                    if zoom_factor > max_zoom:
                        zoom_factor = max_zoom
                elif event.key == pygame.K_DOWN:
                    # 缩小
                    zoom_factor /= 1.1
                    if zoom_factor < min_zoom:
                        zoom_factor = min_zoom
                elif event.key == pygame.K_RIGHT:
                    # 加速
                    speed_index += 1
                    if speed_index > max_speed_index:
                        speed_index = max_speed_index
                    speed_multiplier = speed_factors[speed_index]
                elif event.key == pygame.K_LEFT:
                    # 减速
                    speed_index -= 1
                    if speed_index < 0:
                        speed_index = 0
                    speed_multiplier = speed_factors[speed_index]
            elif event.type == pygame.VIDEORESIZE:
                # 处理窗口大小调整事件
                screen_width, screen_height = event.size
                screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
                # 重新计算边界矩形
                boundary_rect = pygame.Rect(
                    boundary_margin,
                    top_margin,
                    screen_width - 2 * boundary_margin,
                    screen_height - top_margin - slider_height - boundary_margin
                )
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    mouse_x, mouse_y = event.pos
                    # 检查是否点击了速度滑块
                    slider_rect = draw_speed_slider(screen, speed_index, max_speed_index, font)
                    if slider_rect.collidepoint(mouse_x, mouse_y):
                        dragging_speed = True
                    elif boundary_rect.collidepoint(mouse_x, mouse_y):
                        dragging_speed = False
                        dragging = True
                        last_mouse_x, last_mouse_y = event.pos
                    else:
                        dragging = False
                        dragging_speed = False
                elif event.button == 4:  # 滚轮上滚
                    # 放大
                    zoom_factor *= 1.1
                    if zoom_factor > max_zoom:
                        zoom_factor = max_zoom
                elif event.button == 5:  # 滚轮下滚
                    # 缩小
                    zoom_factor /= 1.1
                    if zoom_factor < min_zoom:
                        zoom_factor = min_zoom
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # 左键释放
                    dragging = False
                    dragging_speed = False
            elif event.type == pygame.MOUSEMOTION:
                if dragging:
                    dx, dy = event.rel
                    offset_x += dx
                    offset_y += dy
                elif 'dragging_speed' in locals() and dragging_speed:
                    # 更新速度索引
                    mouse_x, mouse_y = event.pos
                    slider_rect = draw_speed_slider(screen, speed_index, max_speed_index, font)
                    relative_x = mouse_x - slider_rect.x
                    speed_index = int((relative_x / slider_rect.width) * max_speed_index)
                    if speed_index < 0:
                        speed_index = 0
                    if speed_index > max_speed_index:
                        speed_index = max_speed_index
                    speed_multiplier = speed_factors[speed_index]

        screen.fill((255, 255, 255))  # 用白色清屏

        # 根据速度和时间更新当前帧索引
        if not paused:
            # 计算自上次帧的时间
            current_time = time.time()
            elapsed_time = current_time - last_frame_time

            # 根据速度调整帧延迟
            frame_delay = max(0.01, 0.1 / speed_multiplier)  # 在1x速度下，基本延迟为0.1秒

            if elapsed_time >= frame_delay and current_frame_index + 1 < len(frame_reader.frames) and not (
                    current_frame_index == -1 and len(frame_reader.frames) < args.preload):
                last_frame_time = current_time
                current_frame_index += 1

                # 如果是第一帧，调整缩放和偏移量以适应整个棋盘
                if current_frame_index == 0:
                    frame = frame_reader.frames[current_frame_index]
                    width = frame['width']
                    height = frame['height']

                    # 调整缩放比例以适应整个棋盘
                    zoom_factor_x = boundary_rect.width / width
                    zoom_factor_y = boundary_rect.height / height
                    zoom_factor = min(zoom_factor_x, zoom_factor_y)

                    # 确保缩放比例在合理范围内
                    zoom_factor = max(min_zoom, min(zoom_factor, max_zoom))

                    # 居中棋盘
                    offset_x = (boundary_rect.width - width * zoom_factor) / 2
                    offset_y = (boundary_rect.height - height * zoom_factor) / 2

        if current_frame_index >= 0 and current_frame_index < len(frame_reader.frames):
            frame = frame_reader.frames[current_frame_index]

            # 绘制当前帧
            draw_frame(screen, frame, zoom_factor, offset_x, offset_y, boundary_rect, show_grid=True)
            # 显示generation和live cells数量
            draw_text(screen, f"Generation: {frame['generation']}", 10, 50, font)
            draw_text(screen, f"Live Cells: {frame['live_cell_count']}", 10, 80, font)
        else:
            draw_text(screen, "Preloading frames: " + str(len(frame_reader.frames)) + "/" + str(args.preload), 10, 50,
                      font)

        # 绘制标题
        title_text = "Conway's Game of Life"
        title_surface = title_font.render(title_text, True, (0, 0, 0))
        title_rect = title_surface.get_rect()
        title_rect.centerx = screen.get_rect().centerx
        title_rect.y = 10  # 标题距离顶部10像素
        screen.blit(title_surface, title_rect)

        # 绘制速度滑块
        slider_rect = draw_speed_slider(screen, speed_index, max_speed_index, font)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    frame_reader.join()


if __name__ == "__main__":
    main()
