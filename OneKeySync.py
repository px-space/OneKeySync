# -*- coding: utf-8 -*-
'''
版本：beta

处理规则：
1、源存在，目标不存在 -- 复制到目标
2、源存在，目标存在，源较新 -- 覆盖目标
3、源不存在，目标存在 -- 删除目标
4、源存在，目标存在，源为文件夹，目标为文件 -- 删除目标，复制源
5、源存在，目标存在，源为文件，目标为文件夹 -- 删除目标，复制源
'''
import os
import shutil
import sys
import re

fp = ''

# list = sys.argv
source_folder = []
target_folder = []


def createLink():
    ''' 创建磁盘分区到实际路径的链接 '''
    # 同步方向，即SyncFolder的方向
    sync_direction_default = False
    bindingPath_Windows = {
        "files": "f:",
        "backup": "h:"
    }
    bindingPath_Linux = {
        "files": "/run/media/ho/Files",
        "backup": "/run/media/ho/Backup"
    }
    # list = sys.argv
    SyncFolder = [
        "{files}/code{backup}/code",
    ]

    binding = ""
    if os.name == "nt":
        binding = bindingPath_Windows
    else:
        binding = bindingPath_Linux

    for item in SyncFolder:
        tmp = re.split("[{}]", item)
        if sync_direction_default:
            source_folder.append(binding[tmp[1]] + tmp[2])
            target_folder.append(binding[tmp[3]] + tmp[4])
        else:
            source_folder.append(binding[tmp[3]] + tmp[4])
            target_folder.append(binding[tmp[1]] + tmp[2])


class SyncStuct:
    ''' SyncType - - 0：删除文件 1：删除目录 2：复制文件 3：复制目录 '''

    def __init__(self, syncType, syncSrc, syncDes):
        self.SyncType = syncType
        self.SyncSource = syncSrc
        self.SyncTarget = syncDes

    def deal(self):
        dealFunc[self.SyncType](self.SyncSource, self.SyncTarget)

    def show(self):
        return ("%s: %s\t-->  %s\n" % (showString[self.SyncType],
                                       self.SyncSource, self.SyncTarget))


def m_remove(src, des):
    os.remove(src)


def m_removeTree(sec, des):
    shutil.rmtree(sec)


def show():
    """ 查看所有项目 """

    global source_folder
    global target_folder
    print("将同步下列文件夹：")
    print("-------------------------------------")
    for i in range(0, len(source_folder)):
        print("源：%s\t-->  目标：%s" % (source_folder[i], target_folder[i]))


def needCopy(SourceFile, TargetFile):
    ''' 决断是否需要拷贝。如果需要，返回True，否则返回False '''

    if (not os.path.exists(TargetFile)):
        # 目标文件还不存在，当然要拷过去啦
        return True

    if (os.path.isdir(TargetFile)):
        # 目标为文件夹，删除目标，然后返回ture
        shutil.rmtree(TargetFile)
        return True

    # 这里精确度为0.1秒
    from_file_modify_time = round(os.stat(SourceFile).st_mtime, 1)
    # 拿到两边文件的最后修改时间
    to_file_modify_time = round(os.stat(TargetFile).st_mtime, 1)
    if (from_file_modify_time > to_file_modify_time):
        # 比较两边文件的最后修改时间
        return True

    global fp
    if (from_file_modify_time < to_file_modify_time):
        fp.write("检查文件：%s\t--> %s\n" % (SourceFile, TargetFile))
        # return True

    return False


def syncdir(source_folder, target_folder):
    """ 这里递归同步每一个文件夹下的文件 """

    if (not os.path.exists(target_folder)):
        # 目标文件夹不存在，复制整个目录

        # 复制目录
        SyncInfo.append(SyncStuct(3, source_folder, target_folder))
        return

    if not os.path.isdir(target_folder):
        # 目标为文件，删除，复制目录

        # 删除文件
        SyncInfo.append(SyncStuct(0, target_folder, ""))
        # 复制目录
        SyncInfo.append(SyncStuct(3, source_folder, target_folder))
        return

    sourceList = os.listdir(source_folder)
    targetList = os.listdir(target_folder)

    for file in targetList:
        # 遍历目标目录下的所有文件，如果源目录不存在，则删除

        from_file = os.path.join(source_folder, file)
        to_file = os.path.join(target_folder, file)

        if not os.path.exists(from_file):
            if os.path.isdir(to_file):
                # 删除目录
                SyncInfo.append(SyncStuct(1, to_file, ""))
            else:
                # 删除文件
                SyncInfo.append(SyncStuct(0, to_file, ""))

    for file in sourceList:
        # 遍历源文件夹下的所有文件（包括文件夹）。用os.path.walk，或许会更方便些，那样递归都省去了。

        from_file = os.path.join(source_folder, file)
        to_file = os.path.join(target_folder, file)

        if (os.path.isdir(from_file)):
            # 如果是文件夹，递归
            syncdir(from_file, to_file)
        else:
            if (needCopy(from_file, to_file)):
                # 复制文件
                SyncInfo.append(SyncStuct(2, from_file, to_file))


dealFunc = [m_remove, m_removeTree, shutil.copy2, shutil.copytree]
showString = ["删除文件", "删除目录", "复制文件", "复制目录"]
SyncInfo = []

fp = open("sync.log", "w")
if __name__ == '__main__':
    createLink()

    # 再次确认是否同步
    show()

    print("-------------------------------------")
    input("回车开始分析，Ctrl+C 退出")
    for i in range(0, len(source_folder)):
        if not os.path.isdir(source_folder[i]):
            print("文件夹 %s 不存在" % source_folder[i])
            continue
        if not os.path.isdir(target_folder[i]):
            print("文件夹 %s 不存在" % target_folder[i])
            continue
        print('正在分析 %s\t-- %s' % (source_folder[i], target_folder[i]))
        syncdir(source_folder[i], target_folder[i])  # 这里是同步的入口

    print("-------------------------------------")
    if len(SyncInfo) == 0:
        print("分析已完成，所有文件均为最新。。。回车退出")
        input("")
        sys.exit(0)

    print('分析已完成，即将做如下修改：')
    for item in SyncInfo:
        fp.write(item.show())
    fp.close()
    if os.name == "nt":
        os.system("notepad sync.log")
    else:
        os.system("vi sync.log")

    choose = input("按 y 立即做如下修改，否则退出: ")
    if choose == "Y" or choose == "y":
        _count = len(SyncInfo)
        try:
            for i in range(0, _count):
                SyncInfo[i].deal()
                if i % 5 == 0:
                    print("已完成 %5d\t/ %5d" % (i, _count))
            print("已完成 %5d\t/ %5d" % (_count, _count))
        except Exception as e:
            print(e)
        print("修改已完成。。。。回车退出")
        input("")
