import numpy as np
import math


# 判断是否是采样点
def is_sample_pixel(x, y):
    return x % 2 == 0 and y % 2 == 0


# 判断边缘像素
def is_margin_pixel(image, i, j):
    height, width = image.shape
    if i - 1 < 0 or i + 1 >= height or j - 1 < 0 or j + 1 >= width:
        return True
    else:
        return False


# 判断是否是非采样点
def is_non_sample_pixel(x, y):
    return is_non_sample_pixel_first(x, y) or is_non_sample_pixel_second(x, y)


# 判断是否是第一种非采样点
def is_non_sample_pixel_first(x, y):
    return x % 2 == 1 and y % 2 == 1


# 判断是否是第二种非采样点
def is_non_sample_pixel_second(x, y):
    return (x % 2 == 1 and y % 2 == 0) or (x % 2 == 0 and y % 2 == 1)


# 获得整数最低有效位
def get_lowbit(x):
    return x % 2


# 9位整数转位表示
def int2bits9(d):
    s = 0
    if d < 0:
        s = 1
        d = -d
    bits = [0 for i in range(9)]
    bits[0] = s
    for i in range(0, 8):
        bits[8 - i] = d % 2
        d //= 2
    return bits


def bits2int9(bits):
    d = 0
    for bit in bits[1:]:
        d = d * 2 + bit
    if bits[0] == 1:
        d = -d
    return d


def bits2int_u32(bits):
    d = 0
    for bit in bits:
        d = d * 2 + bit
    return d


def int2bits_u32(d):
    bits = [0 for i in range(32)]
    for i in range(0, 32):
        bits[31 - i] = d % 2
        d //= 2
    return bits


def replace_lowbit(d, b):
    if d % 2 == b:
        return d
    elif d % 2 == 0:
        return d + 1
    else:
        return d - 1


# 插值,x为待插值图像，direction为插值方向，postion为插值点
def generate_interpolation_image(x, direction, postion):
    height, width = x.shape
    res = x.copy()
    # 边缘像素不参与插值
    for i in range(1, height - 1):
        for j in range(1, width - 1):
            if postion(i, j):
                res[i][j] = interpolation_pixel(x, i, j, direction)
    return res


# 像素插值
def interpolation_pixel(image, x, y, direction):
    if direction == 0:
        left = image[x][y - 1]
        right = image[x][y + 1]
        up = image[x - 1][y]
        down = image[x + 1][y]
        if is_margin_pixel(image, x, y - 1):
            left = right
        elif is_margin_pixel(image, x, y + 1):
            right = left
        if is_margin_pixel(image, x - 1, y):
            up = down
        elif is_margin_pixel(image, x + 1, y):
            down = up
    elif direction == 45:
        left = image[x - 1][y - 1]
        right = image[x + 1][y + 1]
        up = image[x - 1][y + 1]
        down = image[x + 1][y - 1]
        if is_margin_pixel(image, x - 1, y - 1):
            left = 0
        elif is_margin_pixel(image, x + 1, y + 1):
            right = 0
        if is_margin_pixel(image, x - 1, y + 1):
            up = 0
        elif is_margin_pixel(image, x + 1, y - 1):
            down = 0
        # 0的用其他填充
        vecs = [left, right, up, down]
        for i in range(0, 4):
            for j in range(0, 4):
                if vecs[i] == 0 and vecs[j] != 0:
                    vecs[i] = vecs[j]
        left, right, up, down = vecs
    x0 = (left + right) / 2
    x90 = (up + down) / 2
    u = (left + right + up + down) / 4
    sigma0 = ((left - u) * (left - u) + (x0 - u) * (x0 - u) + (right - u) * (right - u)) / 3
    sigma90 = ((up - u) * (up - u) + (x90 - u) * (x90 - u) + (down - u) * (down - u)) / 3
    if sigma0 == 0 and sigma90 == 0:
        res = u
    else:
        w0 = sigma90 / (sigma90 + sigma0)
        w90 = 1 - w0
        res = w0 * x0 + w90 * x90
    return int(res)


# 计算峰值信噪比
def psnr(x, y):
    squre_sum = np.sum(np.square(x - y))
    mse = squre_sum / (x.shape[0] * x.shape[1])
    result = 20 * math.log10(255 / math.sqrt(mse))
    return result





