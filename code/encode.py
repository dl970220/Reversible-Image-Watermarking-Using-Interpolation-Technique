import utility


# 获得边缘像素 ok
def get_margin_pixel(x):
    height, width = x.shape
    margin_pixels = x[0].tolist() + x[-1].tolist() + x[:, 0][1:height - 1].tolist() + x[:, -1][1:height - 1].tolist()
    margin_bits = [utility.get_lowbit(pixel) for pixel in margin_pixels]
    return margin_bits


# 计算LM，RM，LN，RN ok
def cal_key(difference, condition):
    height, width = difference.shape
    histogram = [0 for i in range(511)]
    for i in range(1, height - 1):
        for j in range(1, width - 1):
            if condition(i, j):
                histogram[difference[i][j] + 255] += 1
    p = q = 0
    for item in histogram:
        if item > histogram[p]:
            q = p
            p = histogram.index(item)
        elif item > histogram[q]:
            q = histogram.index(item)
    lm = p - 255
    rm = q - 255
    if lm > rm:
        lm, rm = rm, lm
    t = p
    for i in range(0, p + 1):
        if histogram[i] < histogram[t]:
            t = i
    ln = t - 255
    t = q
    for i in range(q, len(histogram)):
        if histogram[i] < histogram[t]:
            t = i
    rn = t - 255
    return [lm, rm, ln, rn]


# 编码
def encode(x, information):
    # (1)
    s_lm = s_rm = s_ln = s_rn = 0
    payload = get_margin_pixel(x) + information
    p_size = len(payload)
    p = 0
    height, width = x.shape
    boundary_map = []
    # (2)
    # 非采样点插值
    y = utility.generate_interpolation_image(x, 45, utility.is_non_sample_pixel_first)
    y = utility.generate_interpolation_image(y, 0, utility.is_non_sample_pixel_second)
    # 计算非采样插值误差e
    e = x - y
    # (3)
    ns_lm, ns_rm, ns_ln, ns_rn = cal_key(e, utility.is_non_sample_pixel)
    # (4)
    for i in range(1,  height - 1):
        for j in range(1, width - 1):
            # 先将信息插入非采样像素
            if p < p_size and utility.is_non_sample_pixel(i, j):
                if x[i][j] == 0 or x[i][j] == 255:
                    boundary_map.append(0)
                else:
                    e[i][j], flag = additive_expansion(ns_lm, ns_ln, ns_rm, ns_rn, payload[p], e[i][j])
                    p += flag
                    if y[i][j] + e[i][j] == 0 or y[i][j] + e[i][j] == 255:
                        boundary_map.append(1)
    y += e
    l = len(boundary_map)
    # 非采样像素中载荷数
    np_size = p
    # (5)
    if p < p_size:
        # 利用水印后的非样本像素，生成样本像素
        k = utility.generate_interpolation_image(y, 0, utility.is_sample_pixel)
        e = y - k
        s_lm, s_rm, s_ln, s_rn = cal_key(e, utility.is_sample_pixel)
        for i in range(1, height - 1):
            for j in range(1, width - 1):
                if p < p_size and utility.is_sample_pixel(i, j):
                    # ?
                    if y[i][j] == 0 or y[i][j] == 255:
                        boundary_map.append(0)
                    else:
                        e[i][j], flag = additive_expansion(s_lm, s_ln, s_rm, s_rn, payload[p], e[i][j])
                        p += flag

                        if k[i][j] + e[i][j] == 0 or k[i][j] + e[i][j] == 255:
                            boundary_map.append(1)
        k += e
        y = k
    sp_size = p - np_size
    # 容量不足
    if p < p_size:
        print('容量不足')
        print('最大容量为' + str(p - 2 * width - 2 * height + 4))
        return k
    ###
    print('encode')
    print('ns_lm, ns_ln, ns_rm, ns_rn: {0}, {1}, {2}, {3}'.format(ns_lm, ns_ln, ns_rm, ns_rn))
    print('s_lm, s_ln, s_rm, s_rn: {0}, {1}, {2}, {3}'.format(s_lm, s_ln, s_rm, s_rn))
    print('np_size, sp_size: {0}, {1}'.format(np_size, sp_size))
    print('length: {}'.format(l))
    print('BoundaryMap: {}', boundary_map)
    print('payload: {}'.format(payload))
    # (6)
    # s_lm, s_ln, s_rm, s_rn, ns_lm, ns_ln, ns_rm, ns_rn, l, np_size,sp_size
    s_lm_bits = utility.int2bits9(s_lm)
    s_ln_bits = utility.int2bits9(s_ln)
    s_rm_bits = utility.int2bits9(s_rm)
    s_rn_bits = utility.int2bits9(s_rn)
    ns_lm_bits = utility.int2bits9(ns_lm)
    ns_ln_bits = utility.int2bits9(ns_ln)
    ns_rm_bits = utility.int2bits9(ns_rm)
    ns_rn_bits = utility.int2bits9(ns_rn)
    l_bits = utility.int2bits_u32(l)
    np_size_bits = utility.int2bits_u32(np_size)
    sp_size_bits = utility.int2bits_u32(sp_size)
    overhead = s_lm_bits + s_ln_bits + s_rm_bits + s_rn_bits + ns_lm_bits + ns_ln_bits + ns_rm_bits + ns_rn_bits
    overhead = overhead + l_bits + sp_size_bits + np_size_bits + boundary_map
    # 边界像素不足
    if len(overhead) > (width + height) * 2 - 4:
        print('边界像素不足')
        return y
    i = 1
    while i <= len(overhead):
        if i <= width:
            y[0][i - 1] = utility.replace_lowbit(y[0][i - 1], overhead[i - 1])
        elif i <= 2 * width:
            y[height - 1][i - width - 1] = utility.replace_lowbit(y[height - 1][i - width - 1], overhead[i - 1])
        elif i <= 2 * width + height - 2:
            y[i - 2 * width][0] = utility.replace_lowbit(y[i - 2 * width][0], overhead[i - 1])
        elif i <= 2 * width + 2 * height - 4:
            y[i - 2 * width - height + 2][width - 1] = utility.replace_lowbit(y[i - 2 * width - height + 2][width - 1], overhead[i - 1])
        else:
            print('边缘地区容量不足')
        i += 1
    return y


# 差值扩展 ok
def additive_expansion(lm, ln, rm, rn, b, e):
    flag = 0
    if e <= lm:
        sine = -1
    elif e >= rm:
        sine = 1
    if e == lm or e == rm:
        e += sine * b
        flag = 1
    elif ln < e < lm or rm < e < rn:
        e += sine
    return e, flag

