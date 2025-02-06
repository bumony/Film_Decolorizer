import matplotlib as mpl
import argparse
from matplotlib.pyplot import imshow
import rawpy
import numpy as np
import cv2
import os
from os.path import exists
from os import mkdir
from datetime import datetime

mpl.rcParams['figure.figsize'] = 8, 16


def get_raw(path):
    """
    读取raw文件,我是索尼的ARW，其他的raw文件需要测试
    :param path: 图片路径
    :return:rgb图像
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"文件未找到: {path}")
    with rawpy.imread(path) as raw:
        rgb_image = raw.postprocess(output_color=rawpy.ColorSpace.sRGB)
    return rgb_image


def cvtRGB2BGR(rgb_image):
    return cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)


def cvtRGB2HSV(rgb_image):
    return cv2.cvtColor(rgb_image, cv2.COLOR_RGB2HSV)


def cvtBGR2RGB(bgr_image):
    return cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)


def cvtBGR2HSV(bgr_image):
    return cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)


def cvtHSV2RGB(hsv_image):
    return cv2.cvtColor(hsv_image, cv2.COLOR_HSV2RGB)


def cvtHSV2BGR(hsv_image):
    return cv2.cvtColor(hsv_image, cv2.COLOR_HSV2BGR)


def cvtBGR2GRAY(bgr_image):
    return cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)


def crop_img_xy(bgr_image):
    """
    通过颜色检测裁剪图片, 返回裁剪区域的坐标
    这个函数是用来把翻拍胶卷的外面一圈黑边自动裁切掉的，扫描的图片需要另外实现如何分割图像
    :param bgr_image: opencv处理的bgr图像
    :return: {x, y, w, h}坐标字典
    """
    hsv_image = cvtBGR2HSV(bgr_image)
    lower_black = np.array([0, 0, 0])  # 低阈值 (接近完全黑)
    upper_black = np.array([180, 255, 50])  # 高阈值 (稍微允许一些暗色)
    mask = cv2.inRange(hsv_image, lower_black, upper_black)
    non_black_mask = cv2.bitwise_not(mask)  # 非黑色部分
    contours, _ = cv2.findContours(non_black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        return {
            'x': x,
            'y': y,
            'w': w,
            'h': h
        }
    else:
        return None


def shrink(ix, iy, iw, ih, size=0.9):
    """
    缩小裁剪区域，这里是为了避免黑边和齿孔带来的极黑/极白的影响，缩小裁剪区域
    输入的是crop_img_xy的返回值坐标，在这个坐标基础上缩小裁剪区域
    :param ix: 坐标x
    :param iy: 坐标y
    :param iw: 宽度
    :param ih: 高度
    :param size: 缩小的比例
    :return: 新坐标字典
    """
    shrink_factor = size
    new_w = int(iw * shrink_factor)
    new_h = int(ih * shrink_factor)
    new_x = ix + int(abs(iw - new_w) / 2)
    new_y = iy + int(abs(ih - new_h) / 2)
    # print(ix, iy, iw, ih)
    # print(new_x, new_y, new_w, new_h)
    return {'x': new_x,
            'y': new_y,
            'w': new_w,
            'h': new_h}


def apply_white_balance(image_rgb):
    """
    自动白平衡：根据图像的RGB通道的平均值调整红色、绿色和蓝色通道的增益，使其更自然。
    :param image_rgb: RGB图像
    :return: 调整后的RGB图像
    """
    avg_r = np.mean(image_rgb[:, :, 0])  # 红色通道平均值
    avg_g = np.mean(image_rgb[:, :, 1])  # 绿色通道平均值
    avg_b = np.mean(image_rgb[:, :, 2])  # 蓝色通道平均值

    # 计算所有通道的整体平均值
    avg_all = (avg_r + avg_g + avg_b) / 3.0

    # 计算每个通道的增益系数
    gain_r = avg_all / avg_r
    gain_g = avg_all / avg_g
    gain_b = avg_all / avg_b

    # 调整RGB通道
    image_rgb[:, :, 0] = np.clip(image_rgb[:, :, 0] * gain_r, 0, 255)  # Red通道
    image_rgb[:, :, 1] = np.clip(image_rgb[:, :, 1] * gain_g, 0, 255)  # Green通道
    image_rgb[:, :, 2] = np.clip(image_rgb[:, :, 2] * gain_b, 0, 255)  # Blue通道

    return image_rgb


def auto_color_balance(img):
    """
    归一化自动颜色平衡
    :param img: 
    :return: 
    """
    channels = cv2.split(img)
    out_channels = []
    for channel in channels:
        norm_channel = cv2.normalize(channel, None, 0, 255, cv2.NORM_MINMAX)
        out_channels.append(norm_channel)
    return cv2.merge(out_channels)


def save_img(img, path, type='tif', quality=100):
    """
    保存图片
    :param img: opencv处理的图片
    :param path: 保存路径
    :param type: 保存类型
    :return: 是否保存成功
    """
    if type == 'tif':
        path += '.tif'
        cv2.imwrite(path, img)
        return True
    elif type == 'png':
        path += '.png'
        cv2.imwrite(path, img, [cv2.IMWRITE_PNG_COMPRESSION, quality])
        return True
    else:
        path += '.jpg'
        cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return True


def process_img(input,size):
    try:
        rgb_image = get_raw(input)
        bgr_image = cvtRGB2BGR(rgb_image)  # opencv
        crop_dict = crop_img_xy(bgr_image)  # 裁切
        new_crop_dict = shrink(crop_dict['x'], crop_dict['y'], crop_dict['w'], crop_dict['h'], size)  # 系数看有无齿孔动态调整
        process_tmp_img = bgr_image[new_crop_dict['y']:new_crop_dict['y'] + new_crop_dict['h'],
                          new_crop_dict['x']:new_crop_dict['x'] + new_crop_dict['w']]
        img_inverted = cv2.bitwise_not(process_tmp_img)
        img_color_corrected = auto_color_balance(img_inverted)
        res_img = apply_white_balance(cvtBGR2RGB(img_color_corrected))
        imshow(res_img) # 可以注释掉
        return res_img
    except Exception as e:
        print("Error: ", e)
        return False


def main(root,size, type, quality):
    today = datetime.now().strftime('%Y-%m-%d')

    for root, dirs, files in os.walk(root):
        for file in files:
            if file.endswith('.ARW'):
                input = f'{root}/{file}'
                out_file_name = file.split('.')[0]
                output_dir = f'{root}/{today}_export'
                output = f'{output_dir}/{out_file_name}'
                if not exists(output_dir):
                    mkdir(output_dir)
                res_img = cvtBGR2RGB(process_img(input,size))
                save_img(res_img, output, type, quality)
                print(f"Saved: {output}")


if __name__ == '__main__':
    description = """
    ▗▄▄▄▖▄ █ ▄▄▄▄      ▗▄▄▄  ▗▞▀▚▖▗▞▀▘ ▄▄▄  █  ▄▄▄   ▄▄▄ ▄ ▄▄▄▄▄ ▗▞▀▚▖ ▄▄▄ 
    ▐▌   ▄ █ █ █ █     ▐▌  █ ▐▛▀▀▘▝▚▄▖█   █ █ █   █ █    ▄  ▄▄▄▀ ▐▛▀▀▘█    
    ▐▛▀▀▘█ █ █   █     ▐▌  █ ▝▚▄▄▖    ▀▄▄▄▀ █ ▀▄▄▄▀ █    █ █▄▄▄▄ ▝▚▄▄▖█    
    ▐▌   █ █           ▐▙▄▄▀                █            █                 



                     ▗▄▄▖ ▄   ▄         ▗▄▄▖ █  ▐▌▄▄▄▄   ▄▄▄  ▄▄▄▄         
                     ▐▌ ▐▌█   █         ▐▌ ▐▌▀▄▄▞▘█ █ █ █   █ █   █        
                     ▐▛▀▚▖ ▀▀▀█         ▐▛▀▚▖     █   █ ▀▄▄▄▀ █   █        
                     ▐▙▄▞▘▄   █         ▐▙▄▞▘                              
                           ▀▀▀                                             
    - 小红书：@Bumon_
    - Github: @Bumony
    - 闲鱼：@Bumon
    - 本工具用于负片去色罩，适用于索尼相机拍摄的RAW文件（其他未尝试）                                                                     

    """
    parser = argparse.ArgumentParser(description=description)
    print(description)
    print('运行命令示例：')
    print(
        'python src/main.py --path /Users/bumony/DevSpace/Softwares/Film_Decolorizer/imgs/in --shrink_size 0.9 --type tif --quality 100')
    print('')
    parser.add_argument("--path", help="【必填】需要去色罩负片的输入路径", default='/Users/bumony/DevSpace/Softwares/Film_Decolorizer/imgs/in')  # 这里的默认值为我的调试路径
    parser.add_argument("--shrinkSize", help="【选填】用来裁切掉齿孔，建议0.7-0.9之间取值", default=0.8)
    parser.add_argument("--type", help="请输入 tif/png/jpg，默认tif", default='tif')
    parser.add_argument("--quality", help="请输入图片质量 0-100，默认100", type=int, default=100)
    args = parser.parse_args()
    main(args.path, args.shrinkSize, args.type, args.quality)
