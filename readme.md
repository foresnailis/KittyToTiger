# 猫变虎

## 项目目标

现有两张图片，一只小猫和一只老虎：

![kitty](https://zlisnail.cn/img/kitty.png)

![tiger](https://zlisnail.cn/img/tiger.png)

要求将上图变为下图，并展示中间的渐变过程。

## 代码运行声明

项目仓库：https://github.com/foresnailis/KittyToTiger

参考代码：https://www.csie.ntu.edu.tw/~b97074/vfx_html/hw1.html#C5

python代码文件，需要opencv+numpy库。确保img文件夹下存有kitty.png/tiger.png两图片后，运行该代码，中间帧图片生成在result文件夹下。

本项目不支持自定义特征线、图片、中间帧数量，有兴趣可自行阅读修改代码。

## 具体算法

参考文献：[Feature-Based Image Metamorphosis , SIGGRAPH 1992](http://www.cs.princeton.edu/courses/archive/fall00/cs426/papers/beier92.pdf)

### 特征线与像素点的关系

首先，为两张图画上特征线，如图：

![特征线](https://zlisnail.cn/img/%E7%89%B9%E5%BE%81%E7%BA%BF.png)

左右图相应位置上的特征线共同成对，共九对特征线。特征线的作用在于确定两张图的对应关系。当然，具体的操作需要落实到每个像素点上。那么，该如何确定两张图之间像素点的对应关系呢？

假设现在只设置一对特征线，要将线之间的关系延展到点之间的关系，需要用到uv两个变量。其中，v是点到特征线的距离，u是点到特征线的垂直落点在整条线段的位置，用比例表示。当两张图的两个点对于图中特征线有相同的uv值，则两个像素点是对应的。

![single-line](https://zlisnail.cn/img/single-line.jpg)

![u_and_v](https://zlisnail.cn/img/u_v_math.jpg)

而对于多对特征线，同一个点可能对应另一张图中的多个点，因此需要对这多个点加权，得到最终的对应点。权重公式如下：

![multi-line](https://zlisnail.cn/img/multi-line.jpg)

![weight](https://zlisnail.cn/img/weight.jpg)

![image-20231002051739189](https://zlisnail.cn/img/image-20231002051739189.png)

### 生成中间帧

确定了两张图中像素与像素之间的对应关系之后，我们就可以生成中间帧了。对于中间帧，我们需要使用线性插值法，按照比例生成中间帧的特征线。换句话讲，比如我们要生成一个猫到虎的中间帧，这个中间帧上的特征线的两个顶点坐标、长度、角度，就由相应的猫图和虎图上对应的两条特征线上的顶点坐标、长度、角度相加除以二得到。这是生成一个中间帧的情况，程序中生成了5个中间帧，因此需要按照五分之一等分。

得到中间帧的特征线后，就可以找到中间帧上每个像素点分别在猫图和虎图上的对应像素点。两个像素点有两种色彩值（RGB+alpha），再利用线性插值原理混合它们，即可得到中间帧像素点的色彩值。

> 找到两张图上的像素点后，可能会出现对应像素点的坐标为浮点数。按照道理来讲，数字图像在opencv中，每个像素点的坐标都是整数。如何确定浮点数坐标对应像素的色彩值呢？可以使用双线性插值法。如下图：
>
> ![bilinear](https://zlisnail.cn/img/bilinear.jpg)

## 算法结果



![results_0](https://zlisnail.cn/img/results_0.jpg)![results_1](https://zlisnail.cn/img/results_1.jpg)![results_2](https://zlisnail.cn/img/results_2.jpg)![results_2](https://zlisnail.cn/img/results_3.jpg)![results_4](https://zlisnail.cn/img/results_4.jpg)

