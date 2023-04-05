class decodeError(Exception):
    pass

def decode(encode):
    # decode to original data
    # ==> num_list
    try:
        encode = list(encode)
        num_list=[0]
        i=0
        o=0
        for num in encode:
            num = ord(num)-63
            num_list[i] = num_list[i] + ((num & 0x1f) << (o*5))
            o=o+1
            if (num & 0x20) == 0:
                if num_list[i] & 0x1:
                    num_list[i] = -((num_list[i]>>1) + 1)
                else:
                    num_list[i] = num_list[i]>>1

                num_list[i] = num_list[i]/100000
                i = i + 1
                o=0
                num_list.append(0)

        # transform to lat lng point
        # ==> point_list
        point_list = [[num_list[0],num_list[1]]]
        last_point = point_list[0]
        for i in range(2,len(num_list)-1,2):
            last_point = [last_point[0]+num_list[i],last_point[1]+num_list[i+1]]
            point_list.append(last_point)
        return point_list

    except Exception as e:
        raise decodeError
