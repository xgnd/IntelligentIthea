from typing import List, Dict

import psutil,os,shutil


def cpu_status() -> float:
    return psutil.cpu_percent(interval=1)  # type: ignore


def per_cpu_status() -> List[float]:
    return psutil.cpu_percent(interval=1, percpu=True)  # type: ignore


def memory_status() -> float:
    return psutil.virtual_memory().percent


def disk_usage() -> Dict[str, psutil._common.sdiskusage]:
    disk_parts = [psutil.disk_partitions()[0]]
    disk_usages = {
        d.mountpoint: psutil.disk_usage(d.mountpoint) for d in disk_parts
    }
    return disk_usages

def clean_cache():
    """ 清除缓存图片 """
    image_route = os.path.join(os.getcwd(), "data", "image")
    shutil.rmtree(image_route+"/cache")
    os.makedirs(image_route+"/cache")

def replace_value(request_body,value1,value2):
    """ value1：需要被替换的值，value2：需要替换的值 """
    # 循环字典，获取键、值
    for key, values in request_body.items():
        # 如果是字典，调用自身
        if type(values) == dict:
            replace_value(values,value1,value2)
        # 如果值不是list且是需要被替换的，就替换掉
        elif values == value1:
                request_body[key] = value2
                # return request_body
        else:
            pass

if __name__ == "__main__":
    print(cpu_status())
    print(memory_status())
    print(disk_usage())