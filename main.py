import cv2
import numpy as np


frame_count = 0
leftImage = None
rightImage = None
# leftImageTmp = None
# rightImageTmp = None
height = 0
width = 0
# Color = (0, 255, 0)  # 框框颜色
# Thickness = 2  # 框框粗细
# Shift = 0  # 框框大小（0为正常）


parameter_a = 0.0
parameter_b = 0.0
parameter_p = 0.0

first_image_name = ""
second_image_name = ""
new_image_name = ""

pairs = []

class Line:
    def __init__(self,Px=0.0,Py=0.0,Qx=0.0,Qy=0.0,Mx=0.0,My=0.0,len=0.0,degree=0.0):
        self.P = (Px, Py)  # start
        self.Q = (Qx, Qy)  # end
        self.M = (Mx, My)  # mid
        self.len = len
        self.degree = degree

    def PQtoMLD(self):
        self.M = ((self.P[0] + self.Q[0]) / 2, (self.P[1] + self.Q[1]) / 2)
        tmpx = self.Q[0] - self.P[0]
        tmpy = self.Q[1] - self.P[1]
        self.len = np.sqrt(tmpx * tmpx + tmpy * tmpy)
        self.degree = np.arctan2(tmpy, tmpx)

    def MLDtoPQ(self):
        tmpx = 0.5 * self.len * np.cos(self.degree)
        tmpy = 0.5 * self.len * np.sin(self.degree)
        self.P = (self.M[0] - tmpx, self.M[1] - tmpy)
        self.Q = (self.M[0] + tmpx, self.M[1] + tmpy)

    # def show(self):
    #     print(f"P({self.P[0]}, {self.P[1]}) Q({self.Q[0]}, {self.Q[1]}) M({self.M[0]}, {self.M[1]})")
    #     print(f"len={self.len} degree={self.degree}")

    def Getu(self, X):
        X_P_x = X[0] - self.P[0]
        X_P_y = X[1] - self.P[1]
        Q_P_x = self.Q[0] - self.P[0]
        Q_P_y = self.Q[1] - self.P[1]
        u = ((X_P_x * Q_P_x) + (X_P_y * Q_P_y)) / (self.len * self.len)
        return u

    def Getv(self, X):
        X_P_x = X[0] - self.P[0]
        X_P_y = X[1] - self.P[1]
        Q_P_x = self.Q[0] - self.P[0]
        Q_P_y = self.Q[1] - self.P[1]
        Perp_Q_P_x = Q_P_y
        Perp_Q_P_y = -Q_P_x
        v = ((X_P_x * Perp_Q_P_x) + (X_P_y * Perp_Q_P_y)) / self.len
        return v

    def Get_Point(self, u, v):
        Q_P_x = self.Q[0] - self.P[0]
        Q_P_y = self.Q[1] - self.P[1]
        Perp_Q_P_x = Q_P_y
        Perp_Q_P_y = -Q_P_x
        Point_x = self.P[0] + u * (self.Q[0] - self.P[0]) + ((v * Perp_Q_P_x) / self.len)
        Point_y = self.P[1] + u * (self.Q[1] - self.P[1]) + ((v * Perp_Q_P_y) / self.len)
        return Point_x, Point_y

    def Get_Weight(self, X):
        a = parameter_a
        b = parameter_b
        p = parameter_p
        d = 0.0
        u = self.Getu(X)
        if u > 1.0:
            d = np.sqrt((X[0] - self.Q[0]) * (X[0] - self.Q[0]) + (X[1] - self.Q[1]) * (X[1] - self.Q[1]))
        elif u < 0:
            d = np.sqrt((X[0] - self.P[0]) * (X[0] - self.P[0]) + (X[1] - self.P[1]) * (X[1] - self.P[1]))
        else:
            d = abs(self.Getv(X))
        weight = (self.len ** p) / (a + d) ** b

        return weight

class LinePair:
    def __init__(self):
        self.leftLine = Line()
        self.rightLine = Line()
        self.warpLine = []

    def genWarpLine(self):
        while self.leftLine.degree - self.rightLine.degree > np.pi:
            self.rightLine.degree += np.pi
        while self.rightLine.degree - self.leftLine.degree > np.pi:
            self.leftLine.degree += np.pi
        for i in range(frame_count):
            ratio = (i + 1) / (frame_count + 1)
            curLine = Line()
            curLine.M = ((1 - ratio) * self.leftLine.M[0] + ratio * self.rightLine.M[0],
                         (1 - ratio) * self.leftLine.M[1] + ratio * self.rightLine.M[1])
            curLine.len = (1 - ratio) * self.leftLine.len + ratio * self.rightLine.len
            curLine.degree = (1 - ratio) * self.leftLine.degree + ratio * self.rightLine.degree
            curLine.MLDtoPQ()
            self.warpLine.append(curLine)

    # def showWarpLine(self):
    #     global leftImageTmp
    #     global rightImageTmp
    #     size = len(self.warpLine)
    #     for i in range(size):
    #         print(f"warpLine[{i}]:")
    #         self.warpLine[i].show()
    #         cv2.line(leftImage, (int(self.warpLine[i].P[0]), int(self.warpLine[i].P[1])),
    #                  (int(self.warpLine[i].Q[0]), int(self.warpLine[i].Q[1])), Color, Thickness, cv2.LINE_AA, Shift)
    #         cv2.line(rightImage, (int(self.warpLine[i].P[0]), int(self.warpLine[i].P[1])),
    #                  (int(self.warpLine[i].Q[0]), int(self.warpLine[i].Q[1])), Color, Thickness, cv2.LINE_AA, Shift)
    #     leftImageTmp = leftImage.copy()
    #     rightImageTmp = rightImage.copy()


class Image:
    def __init__(self, i):
        self.frame_index = i
        # 创建一个133x134的带有Alpha通道的全零图像
        width, height = 133, 134
        channels = 4  # 4通道，包括BGR和Alpha
        # 创建一个全零矩阵，数据类型为uint8，初始值都为0
        self.new_image = np.zeros((height, width, channels), dtype=np.uint8)
        # 设置Alpha通道的值为255，表示完全不透明
        self.new_image[:, :, 3] = 255


    def bilinear(self, image, X, Y):
        x_floor = int(X)
        y_floor = int(Y)
        x_ceil = x_floor + 1
        y_ceil = y_floor + 1
        a = X - x_floor
        b = Y - y_floor
        if x_ceil >= width - 1:
            x_ceil = width - 1
        if y_ceil >= height - 1:
            y_ceil = height - 1
        output_scalar = [0, 0, 0, 0]
        leftdown = image[y_floor, x_floor]
        lefttop = image[y_ceil, x_floor]
        rightdown = image[y_floor, x_ceil]
        righttop = image[y_ceil, x_ceil]
        for i in range(4):
            output_scalar[i] = (1 - a) * (1 - b) * leftdown[i] + a * (1 - b) * rightdown[i] + a * b * righttop[i] + (
                    1 - a) * b * lefttop[i]
        return tuple(output_scalar)

    def Warp(self):
        global leftImage, rightImage, height, width
        # global leftImageTmp, rightImageTmp
        ratio = (self.frame_index + 1) / (frame_count + 1)
        ori_leftImage = cv2.imread(first_image_name,cv2.IMREAD_UNCHANGED)
        ori_rightImage = cv2.imread(second_image_name,cv2.IMREAD_UNCHANGED)

        for x in range(width):
            for y in range(height):
                dst_point = (x, y)
                leftXSum_x = 0.0
                leftXSum_y = 0.0
                leftWeightSum = 0.0
                rightXSum_x = 0.0
                rightXSum_y = 0.0
                rightWeightSum = 0.0
                for i in range(len(pairs)):
                    src_line = pairs[i].leftLine
                    dst_line = pairs[i].warpLine[self.frame_index]

                    new_u = dst_line.Getu(dst_point)
                    new_v = dst_line.Getv(dst_point)
                    src_point = src_line.Get_Point(new_u, new_v)
                    src_weight = dst_line.Get_Weight(dst_point)
                    leftXSum_x += src_point[0] * src_weight
                    leftXSum_y += src_point[1] * src_weight
                    leftWeightSum += src_weight

                    src_line = pairs[i].rightLine
                    new_u = dst_line.Getu(dst_point)
                    new_v = dst_line.Getv(dst_point)
                    src_point = src_line.Get_Point(new_u, new_v)
                    src_weight = dst_line.Get_Weight(dst_point)
                    rightXSum_x += src_point[0] * src_weight
                    rightXSum_y += src_point[1] * src_weight
                    rightWeightSum += src_weight

                left_src_x = leftXSum_x / leftWeightSum
                left_src_y = leftXSum_y / leftWeightSum
                right_src_x = rightXSum_x / rightWeightSum
                right_src_y = rightXSum_y / rightWeightSum

                if left_src_x < 0:
                    left_src_x = 0
                if left_src_y < 0:
                    left_src_y = 0
                if left_src_x >= width:
                    left_src_x = width - 1
                if left_src_y >= height:
                    left_src_y = height - 1
                if right_src_x < 0:
                    right_src_x = 0
                if right_src_y < 0:
                    right_src_y = 0
                if right_src_x >= width:
                    right_src_x = width - 1
                if right_src_y >= height:
                    right_src_y = height - 1

                left_scalar = self.bilinear(ori_leftImage, left_src_x, left_src_y)
                right_scalar = self.bilinear(ori_rightImage, right_src_x, right_src_y)
                new_scalar = (
                    (1 - ratio) * left_scalar[0] + ratio * right_scalar[0],
                    (1 - ratio) * left_scalar[1] + ratio * right_scalar[1],
                    (1 - ratio) * left_scalar[2] + ratio * right_scalar[2],
                    (1 - ratio) * left_scalar[3] + ratio * right_scalar[3]
                )
                self.new_image[y, x] = new_scalar


        # win_name = f"frame[{self.frame_index}]"
        img_name = f"{new_image_name}_{self.frame_index}.jpg"
        # cv2.imshow(win_name, self.new_image)
        cv2.imwrite(img_name, self.new_image)

def genLinePair():
    global pairs
    linepair1=LinePair();
    linepair1.leftLine=Line(31,61,42,73,36.5,67,16.3,0.829)
    linepair1.rightLine=Line(37,51,45,60,41,55.5,12.04,0.844)
    linepair1.genWarpLine()
    pairs.append(linepair1)

    linepair2=LinePair();
    linepair2.leftLine=Line(79,69,64,74,71.5,71.5,15.8,2.820)
    linepair2.rightLine=Line(84,55,70,60,77,57.5,14.87,2.799)
    linepair2.genWarpLine()
    pairs.append(linepair2)

    linepair3=LinePair();
    linepair3.leftLine=Line(20,63,34,98,27,80.5,37.7,1.19)
    linepair3.rightLine=Line(28,62,36,99,32,80.5,37.85,1.358)
    linepair3.genWarpLine()
    pairs.append(linepair3)

    linepair4=LinePair();
    linepair4.leftLine=Line(95,74,77,99,86,86.5,30.81,2.195)
    linepair4.rightLine=Line(106,62,86,98,96,80,41.18,2.078)
    linepair4.genWarpLine()
    pairs.append(linepair4)

    linepair5=LinePair();
    linepair5.leftLine=Line(44,100,58,99,51,99.5,14.04,-0.071)
    linepair5.rightLine=Line(49,99,68,100,58.5,99.5,19.03,0.053)
    linepair5.genWarpLine()
    pairs.append(linepair5)

    linepair6=LinePair();
    linepair6.leftLine=Line(9,14,13,36,11,25,22.4,1.391)
    linepair6.rightLine=Line(22,14,25,32,23.5,23,18.25,1.406)
    linepair6.genWarpLine()
    pairs.append(linepair6)

    linepair7=LinePair();
    linepair7.leftLine=Line(16,14,37,27,26.5,20.5,24.7,0.554)
    linepair7.rightLine=Line(29,13,43,24,36,18.5,17.80,0.666)
    linepair7.genWarpLine()
    pairs.append(linepair7)

    linepair8=LinePair();
    linepair8.leftLine=Line(104,17,75,29,89.5,23,31.4,2.749)
    linepair8.rightLine=Line(96,14,78,23,87,18.5,20.12,2.678)
    linepair8.genWarpLine()
    pairs.append(linepair8)

    linepair9=LinePair();
    linepair9.leftLine=Line(113,23,108,48,110.5,35.5,25.50,1.768)
    linepair9.rightLine=Line(104,20,104,40,104,30,20,1.571)
    linepair9.genWarpLine()
    pairs.append(linepair9)
def runWarp():
    for i in range(frame_count):
        curImage = Image(i)
        print(f"warping {i}...")
        curImage.Warp()


if __name__ == "__main__":

    first_image_name = "img/kitty.png"
    second_image_name = "img/tiger.png"
    frame_count = 5
    new_image_name = "result/results"

    parameter_a = 1
    parameter_b = 2
    parameter_p = 0

    leftImage = cv2.imread(first_image_name,cv2.IMREAD_UNCHANGED)
    rightImage = cv2.imread(second_image_name,cv2.IMREAD_UNCHANGED)
    height = leftImage.shape[0]
    width = leftImage.shape[1]
    # leftImageTmp = leftImage.copy()
    # rightImageTmp = rightImage.copy()
    genLinePair()
    runWarp()

