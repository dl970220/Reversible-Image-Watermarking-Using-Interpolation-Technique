import utility


def get_overhead(x):
    height, width = x.shape
    overhead = x[0].tolist() + x[height - 1].tolist()
    overhead = overhead + x[:, 0][1:height - 1].tolist() + x[:, width - 1][1: height - 1].tolist()
    overhead = [utility.get_lowbit(pixel) for pixel in overhead]
    return overhead


def recover(e, lm, ln, rm, rn, payload):
    t = 0
    if e == lm or e == rm:
        payload.append(0)
        t = 1
    elif e == lm - 1 or e == rm + 1:
        payload.append(1)
        t = 1
    if e == lm or e == lm - 1:
        e += payload[-1]
    elif e == rm or e == rm + 1:
        e -= payload[-1]
    elif ln <= e < lm - 1:
        e += 1
    elif rm + 1 < e <= rn:
        e -= 1
    return e, t


def recover_margin(x, margin_bits):
    height, width = x.shape
    k = 0
    for i in range(width):
        x[0][i] = utility.replace_lowbit(x[0][i], margin_bits[k])
        k += 1
    for i in range(width):
        x[height - 1][i] = utility.replace_lowbit(x[height - 1][i], margin_bits[k])
        k += 1
    for i in range(1, height - 1):
        x[i][0] = utility.replace_lowbit(x[i][0], margin_bits[k])
        k += 1
    for i in range(1, height - 1):
        x[i][width - 1] = utility.replace_lowbit(x[i][width - 1], margin_bits[k])
        k += 1
    return x


# 对y解码
def decode(y):
    # (1)
    s_payload = []
    ns_payload = []
    height, width = y.shape
    overhead = get_overhead(y)
    s_lm_bits = overhead[0:9]
    s_lm = utility.bits2int9(s_lm_bits)
    s_ln_bits = overhead[9:18]
    s_ln = utility.bits2int9(s_ln_bits)
    s_rm_bits = overhead[18:27]
    s_rm = utility.bits2int9(s_rm_bits)
    s_rn_bits = overhead[27:36]
    s_rn = utility.bits2int9(s_rn_bits)
    ns_lm_bits = overhead[36:45]
    ns_lm = utility.bits2int9(ns_lm_bits)
    ns_ln_bits = overhead[45:54]
    ns_ln = utility.bits2int9(ns_ln_bits)
    ns_rm_bits = overhead[54:63]
    ns_rm = utility.bits2int9(ns_rm_bits)
    ns_rn_bits = overhead[63:72]
    ns_rn = utility.bits2int9(ns_rn_bits)
    l_bits = overhead[72:104]
    l = utility.bits2int_u32(l_bits)
    sp_size_bits = overhead[104:136]
    sp_size = utility.bits2int_u32(sp_size_bits)
    np_size_bits = overhead[136:168]
    np_size = utility.bits2int_u32(np_size_bits)
    boundary_map = overhead[168:-1]
    # (2)
    if sp_size != 0:
        # (3) 提取采样像素中的载荷
        b_index = l
        p = 0
        for i in range(1, height - 1):
            for j in range(1, width - 1):
                # 采样像素到某个点必定提取完，若某后不终止继续插，就是找新的，那后面就全是垃圾了
                # (4)
                if utility.is_sample_pixel(i, j) and p < sp_size:
                    # 获得插值e'
                    inter_pixel = utility.interpolation_pixel(y, i, j, 0)
                    e = y[i][j] - inter_pixel
                    if 0 < y[i][j] < 255:
                        e, temp = recover(e, s_lm, s_ln, s_rm, s_rn, s_payload)
                        # 恢复采样像素
                        y[i][j] = inter_pixel + e
                        p += temp
                    else:
                        if boundary_map[b_index] != 0:
                            e, temp = recover(e, s_lm, s_ln, s_rm, s_rn, s_payload)
                            # 恢复采样像素
                            y[i][j] = inter_pixel + e
                            p += temp
                        b_index += 1
    p = 0
    b_index = 0
    # inter_y中含有原始采样像素，和第一类非采样像素的插值值
    inter_y = utility.generate_interpolation_image(y, 45, utility.is_non_sample_pixel_first)
    inter_y = utility.generate_interpolation_image(inter_y, 0, utility.is_non_sample_pixel_second)
    for i in range(1, height - 1):
        for j in range(1, width - 1):
            # 此时判断载荷是否完全被提取得看是否有采样像素水印，若有，则进行到底，没有则容量够了停止
            if (p < np_size or sp_size != 0) and utility.is_non_sample_pixel(i, j):
                inter_pixel = inter_y[i][j]
                e = y[i][j] - inter_pixel
                if 0 < y[i][j] < 255:
                    e, temp = recover(e, ns_lm, ns_ln, ns_rm, ns_rn, ns_payload)
                    # 恢复
                    y[i][j] = inter_pixel + e
                    p += temp
                else:
                    if boundary_map[b_index] != 0:
                        e, temp = recover(e, ns_lm, ns_ln, ns_rm, ns_rn, ns_payload)
                        # 恢复
                        y[i][j] = inter_pixel + e
                        p += temp
                    b_index += 1
    payload = ns_payload + s_payload
    margin_len = (width + height) * 2 - 4
    margin_bits = payload[0: margin_len]
    # 恢复原始图像
    y = recover_margin(y, margin_bits)
    ###
    print('decode')
    print('ns_lm, ns_ln, ns_rm, ns_rn: {0}, {1}, {2}, {3}'.format(ns_lm, ns_ln, ns_rm, ns_rn))
    print('s_lm, s_ln, s_rm, s_rn: {0}, {1}, {2}, {3}'.format(s_lm, s_ln, s_rm, s_rn))
    print('np_size, sp_size: {0}, {1}'.format(np_size, sp_size))
    print('length: {}'.format(l))
    print('BoundaryMap: {}', boundary_map)
    print('payload: {}'.format(payload))
    return y
