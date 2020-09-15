# -*- coding:utf-8 -*-
"""
@Time : 2020/4/19 5:06 下午
@Author : Domionlu
@Site : 
@File : aio.py
"""
import asyncio
import time
async def aa():
    print("我们的门又坏了")
    time.sleep(10)
    print("怎么办啊")

async def fun1():
    print("增强体育锻炼，提高免疫力")
    await asyncio.sleep(5)
    print("才能保证身体健康，诸事顺利")
async def fun2():
    print("这个周末天气不错")
    await asyncio.sleep(3)
    print("可是你就是不想出去")

async def min():
    f1 = asyncio.create_task(fun1())
    f2 = asyncio.create_task(fun2())
    await asyncio.gather(f1,f2)

if __name__ == "__main__":
    asyncio.run(min())
