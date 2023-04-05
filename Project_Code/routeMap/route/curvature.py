from numpy import round
import math


def calculate_circular(point1, point2, point3):
    r1 = round([point1[0] - point2[0], point1[1]-point2[1]], 13)
    r2 = round([point2[0] - point3[0], point2[1]-point3[1]], 13)
    if r1[0]*r2[1] == r1[1]*r2[0]:
        return 2
    else:
        e = 2*(point2[0]-point1[0])
        f = 2*(point2[1]-point1[1])
        g = math.pow(point2[0], 2)-math.pow(point1[0], 2) + \
            math.pow(point2[1], 2)-math.pow(point1[1], 2)
        a = 2*(point3[0]-point2[0])
        b = 2*(point3[1]-point2[1])
        c = math.pow(point3[0], 2)-math.pow(point2[0], 2) + \
            math.pow(point3[1], 2)-math.pow(point2[1], 2)
        X = (g*b-c*f)/(e*b-a*f)

        Y = (a*g-c*e)/(a*f-b*e)
        R = (X-point1[0])*(X-point1[0])+(Y-point1[1])*(Y-point1[1])
        return R**0.5


def road_section(data):
    section = [2]
    for i in range(0, len(data)-2):
        try:
            temp = calculate_circular(data[i], data[i+1], data[i+2])
        except:
            temp = 2
        section.append(temp)
    section.append(2)
    return section

def dangerous(length:int)->int:
    if length < 0.00022525:
        return 2
    elif length < 0.0004505:
        return 1
    else:
        return 0

def road_dangerous(data):
    data = road_section(data)
    data.pop(0)
    last = dangerous(data[0])
    reslut = []
    count = 0
    
    for i in data:
        danger = dangerous(i)
        if danger == last:
            count = count +1
        else:
            reslut.append([count,last])
            count = 1
            last = danger
    reslut.append([count,last])

    return reslut
