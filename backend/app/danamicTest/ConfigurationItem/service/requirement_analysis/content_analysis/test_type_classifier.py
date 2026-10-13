# 函数功能：判断测试类型，输出对应的类型标识
# 函数输入：ceshixiang_name 例：接口测试
# 函数输出：ceshixiang_bianhao 例：IF
def ceshi_leixing_biaoshi_choose(ceshixiang_name):
    if  '接口' in ceshixiang_name or '接收' in ceshixiang_name or '发送' in ceshixiang_name:
        ceshixiang_bianhao = 'IF'
        ceshileixing='接口测试'
    elif '性能' in ceshixiang_name or '时间' in ceshixiang_name:
        ceshixiang_bianhao = 'PF'
        ceshileixing = '性能测试'
    elif '边界' in ceshixiang_name:
        ceshixiang_bianhao = 'BD'
        ceshileixing = '边界测试'
    elif '安全' in ceshixiang_name:
        ceshixiang_bianhao = 'SE'
        ceshileixing = '安全性测试'
    elif '余量' in ceshixiang_name:
        ceshixiang_bianhao = 'AL'
        ceshileixing = '余量测试'
    elif '强度' in ceshixiang_name:
        ceshixiang_bianhao = 'RB'
        ceshileixing = '强度测试'
    elif '恢复' in ceshixiang_name:
        ceshixiang_bianhao = 'RC'
        ceshileixing = '恢复性测试'
    elif '容量' in ceshixiang_name:
        ceshixiang_bianhao = 'CA'
        ceshileixing = '容量测试'
    elif '人机' in ceshixiang_name or '交互' in ceshixiang_name:
        ceshixiang_bianhao = 'RC'
        ceshileixing = '人机交互界面测试'
    else:
        ceshixiang_bianhao = 'FN'
        ceshileixing = '功能测试'
    ceshixiang_bianhao = '-'+ceshixiang_bianhao+'01'
    return ceshixiang_bianhao,ceshileixing


# 函数功能： 测试项与测数据库中测试内容的匹配
# 函数输入：ceshixiang_result_dict：测试项数据库的内容包含测试项名称测试内容以及测试方法
# 函数输入：cehisixiang_name_temp： 测试项名称
# 函数输出：ceshixiang_miaoshu, ceshixiang_fangfa, ceshixiang_find：测试项数据库中对应的测试内容，测试方法，是否找到对应测试项
# 特殊处理：对带有（性能测试）、（边界测试）、（容量测试）的进行特殊处理
def ceshixiang_pipei(ceshixiang_result_dict,cehisixiang_name_temp):
    ceshixiang_miaoshu=''
    ceshixiang_fangfa=''
    ceshixiang_find=0
    # 遍历测试项数据库从数据库开始查找
    for item_temp in ceshixiang_result_dict:
        # 对于拆分出来的性能测试，边界测试和容量测试等，需要进行特殊处理。
        if '性能测试' in cehisixiang_name_temp:
            if '性能' not in item_temp:
                continue
        elif '边界测试' in cehisixiang_name_temp:
            if '边界' not in item_temp:
                continue
        elif '容量测试' in cehisixiang_name_temp:
            if '容量' not in item_temp:
                continue
        if '&' in item_temp:
            item_temp_fenge = item_temp.split('&')
            if len(item_temp_fenge) == 2:
                if item_temp_fenge[0] in cehisixiang_name_temp and item_temp_fenge[1] in cehisixiang_name_temp:
                    ceshixiang_miaoshu, ceshixiang_fangfa = ceshixiang_result_dict[item_temp]
                    ceshixiang_find = 1
                    break
            elif len(item_temp_fenge) == 3:
                if item_temp_fenge[0] in cehisixiang_name_temp and item_temp_fenge[1] in cehisixiang_name_temp and \
                        item_temp_fenge[2] in cehisixiang_name_temp:
                    ceshixiang_miaoshu, ceshixiang_fangfa = ceshixiang_result_dict[item_temp]
                    ceshixiang_find = 1
                    break
            else:
                if item_temp_fenge[0] in cehisixiang_name_temp:
                    ceshixiang_miaoshu, ceshixiang_fangfa = ceshixiang_result_dict[item_temp]
                    ceshixiang_find = 1
                    break
        elif '||' in item_temp:
            item_temp_fenge = item_temp.split('||')
            if len(item_temp_fenge) == 2:
                if item_temp_fenge[0] in cehisixiang_name_temp or item_temp_fenge[1] in cehisixiang_name_temp:
                    ceshixiang_miaoshu, ceshixiang_fangfa = ceshixiang_result_dict[item_temp]
                    ceshixiang_find = 1
                    break
            elif len(item_temp_fenge) == 3:
                if item_temp_fenge[0] in cehisixiang_name_temp or item_temp_fenge[1] in cehisixiang_name_temp or \
                        item_temp_fenge[2] in cehisixiang_name_temp:
                    ceshixiang_miaoshu, ceshixiang_fangfa = ceshixiang_result_dict[item_temp]
                    ceshixiang_find = 1
                    break
            else:
                if item_temp_fenge[0] in cehisixiang_name_temp:
                    ceshixiang_miaoshu, ceshixiang_fangfa = ceshixiang_result_dict[item_temp]
                    ceshixiang_find = 1
                    break
        else:
            if item_temp in cehisixiang_name_temp:
                ceshixiang_miaoshu, ceshixiang_fangfa = ceshixiang_result_dict[item_temp]
                ceshixiang_find = 1
                break
    return ceshixiang_miaoshu, ceshixiang_fangfa, ceshixiang_find
