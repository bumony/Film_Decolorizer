## 介绍
写这个小脚本的目的是：懒，为了能比较方便处理我翻拍的胶片底片，能一次对整个目录的底片进行去色罩操作，并且导tif格式的图以便后续修改。


## 原理/流程
- 先对图片识别最大的矩形区域进行裁剪
- 通过系数把图片周边一圈的齿孔/片基裁掉剩下纯净图像
- 3个通道色相反向
- 归一化颜色平衡+自动白平衡
- 导出tif照片到子目录（若没有输入参数）


## 初始化
### 配置python环境
```shell

```
### 安装依赖
```shell
pip install -r requirements.txt
```

## 运行
### 参数
```python
parser.add_argument("--path", help="【必填】需要去色罩负片的输入路径", default='/Users/bumony/DevSpace/Softwares/Film_Decolorizer/imgs/in')  # 这里的默认值为我的调试路径
parser.add_argument("--shrinkSize", help="【选填】用来裁切掉齿孔，建议0.7-0.9之间取值", default=0.8)
parser.add_argument("--type", help="请输入 tif/png/jpg，默认tif", default='tif')
parser.add_argument("--quality", help="请输入图片质量 0-100，默认100", type=int, default=100)
```
- 路径 我这里是MacOS的系统，win系统未测试，如果有bash之类的终端的话单斜杠也行
- 缩放的size 用来裁切掉齿孔和片基，建议0.7-0.9之间取值
- 导出格式 默认tif，可选png/jpg
- 导出质量 默认100，在格式为png/jpg的时候生效
### sh运行
```shell
cd your/path/to/Film_Decolorizer/src # 替换为你自己的目录
python main.py --path /Users/bumony/DevSpace/Softwares/Film_Decolorizer/imgs/in --shrinkSize 0.8 --type tif --quality 100
```
⬆️可以写成一个shell脚本或者cmd脚本来调用python文件，输出的目录会在输入目录下建一个日期文件夹

---
放了几张raw在 `imgs/in` 目录下，可以用来测试


希望这个小脚本能帮到你，如果有问题欢迎提issue，如果有更好的建议欢迎提pr，谢谢！
小红书：Bumon_
```