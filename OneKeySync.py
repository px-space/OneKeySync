# -*- coding: utf-8 -*-
'''
OneKeySync
python3练习

sync.config.json:
{
    'reverse':false,
    'win_define':{
        'doc':'f:/document/'
    },
    'linux_define':{
        'doc':'/root/document/'
    },
    'folder':[
        '%doc%/abc:%doc%/cde'
    ]
}

处理规则：
1、源存在，目标不存在 -- 复制到目标
2、源存在，目标存在，源较新 -- 覆盖目标
3、源不存在，目标存在 -- 删除目标
4、源存在，目标存在，源为文件夹，目标为文件 -- 删除目标，复制源
5、源存在，目标存在，源为文件，目标为文件夹 -- 删除目标，复制源
'''
import json
import os
import shutil
import sys

default_config_path = 'sync.config.json'
log_file = 'log.txt'


class SyncStuct:
    ''' SyncType - - 0：删除文件 1：删除目录 2：复制文件 3：复制目录 '''
    type_rmfile = 'rmfile'
    type_rmdir = 'rmdir'
    type_cpfile = 'cpfile'
    type_cpdir = 'cpdir'

    showName = {
        'rmfile': '删除文件',
        'rmdir': '删除目录',
        'cpfile': '复制文件',
        'cpdir': '复制目录',
    }
    dealFunc = {
        'rmfile': lambda src, dst: os.remove(src),
        'rmdir': lambda src, dst: shutil.rmtree(src),
        'cpfile': shutil.copy2,
        'cpdir': shutil.copytree,
    }

    def __init__(self, syncType, syncSrc, syncDes):
        self.SyncType = syncType
        self.SyncSource = syncSrc
        self.SyncTarget = syncDes

    def deal(self):
        dealFunc[self.SyncType](self.SyncSource, self.SyncTarget)

    def show(self):
        return ("%s: %s\t-->  %s\n" % (self.showName[self.SyncType], self.SyncSource, self.SyncTarget))


class SyncMethod:
    ' 同步操作 '

    @staticmethod
    def show(info):
        """ 查看所有项目 """

        info = list(info)
        print("将同步下列文件夹：")
        print("-------------------------------------")
        for i in range(0, len(info[0])):
            print("源：%s\t-->  目标：%s" % (info[0][i], info[1][i]))

    @staticmethod
    def loadConfig():
        ' 加载配置文件 '

        with open(default_config_path, 'r', encoding='utf-8') as f:
            buf = f.read()

        return json.loads(buf)

    @staticmethod
    def createLink():
        ''' 创建磁盘分区到实际路径的链接 '''

        source_folder = []
        target_folder = []
        conf = loadConfig()

        # 同步方向，即SyncFolder的方向
        sync_direction_default = bool(conf['reverse'])
        bindingPath_Windows = dict(conf['win_define'])
        bindingPath_Linux = dict(conf['linux_define'])
        SyncFolder = list(conf['folder'])

        binding = ""
        if os.name == "nt":
            binding = bindingPath_Windows
        else:
            binding = bindingPath_Linux

        for item in SyncFolder:
            tmp = re.split("%:", item)
            if sync_direction_default:
                source_folder.append(binding[tmp[1]] + tmp[2])
                target_folder.append(binding[tmp[3]] + tmp[4])
            else:
                source_folder.append(binding[tmp[3]] + tmp[4])
                target_folder.append(binding[tmp[1]] + tmp[2])

        return [source_folder, target_folder]

    @staticmethod
    def needCopy(src_file, dst_file):
        ''' 决定是否需要拷贝。如果需要，返回True，否则返回False '''

        if (not os.path.exists(dst_file)):
            # 目标文件还不存在，当然要拷过去啦
            return True

        if (os.path.isdir(dst_file)):
            # 目标为文件夹，删除目标，然后返回ture
            shutil.rmtree(dst_file)
            return True

        # 这里精确度为0.1秒
        from_file_modify_time = round(os.stat(src_file).st_mtime, 1)
        # 拿到两边文件的最后修改时间
        to_file_modify_time = round(os.stat(dst_file).st_mtime, 1)
        if (from_file_modify_time > to_file_modify_time):
            # 比较两边文件的最后修改时间
            return True

        if (from_file_modify_time < to_file_modify_time):
            return None

        return False

    @staticmethod
    def syncdir(src, dst):
        """ 这里递归同步每一个文件夹下的文件 """

        SyncInfo = []

        if (not os.path.exists(dst)):
            # 目标文件夹不存在，复制整个目录

            # 复制目录
            SyncInfo.append(SyncStuct(3, src, dst))
            return

        if not os.path.isdir(dst):
            # 目标为文件，删除，复制目录

            # 删除文件
            SyncInfo.append(SyncStuct(SyncStuct.type_rmfile, dst, ""))
            # 复制目录
            SyncInfo.append(SyncStuct(SyncStuct.type_cpdir, src, dst))
            return

        sourceList = os.listdir(src)
        targetList = os.listdir(dst)

        for file in targetList:
            # 遍历目标目录下的所有文件，如果源目录不存在，则删除

            from_file = os.path.join(src, file)
            to_file = os.path.join(dst, file)

            if not os.path.exists(from_file):
                if os.path.isdir(to_file):
                    # 删除目录
                    SyncInfo.append(
                        SyncStuct(SyncStuct.type_rmdir, to_file, ""))
                else:
                    # 删除文件
                    SyncInfo.append(
                        SyncStuct(SyncStuct.type_rmfile, to_file, ""))

        for file in sourceList:
            # 遍历源文件夹下的所有文件（包括文件夹）。用os.path.walk，或许会更方便些，那样递归都省去了。

            from_file = os.path.join(src, file)
            to_file = os.path.join(dst, file)

            if (os.path.isdir(from_file)):
                # 如果是文件夹，递归
                syncdir(from_file, to_file)
            else:
                r = needCopy(from_file, to_file)
                if r == True:
                    # 复制文件
                    SyncInfo.append(
                        SyncStuct(SyncStuct.type_cpfile, from_file, to_file))

        return SyncInfo

    @staticmethod
    def doAnalyse(info):
        info = list(info)
        source_folder, target_folder = info[0], info[1]
        result = []

        for i in range(0, len(source_folder)):
            if not os.path.isdir(source_folder[i]):
                print("文件夹 %s 不存在" % source_folder[i])
                continue
            if not os.path.isdir(target_folder[i]):
                print("文件夹 %s 不存在" % target_folder[i])
                continue
            print('正在分析 %s\t-- %s' % (source_folder[i], target_folder[i]))
            result += syncdir(source_folder[i], target_folder[i])  # 这里是同步的入口

        return result

    @staticmethod
    def doSync(action):
        action = list(action)
        count = len(action)
        i = 1
        for it in action:
            it = SyncStuct(it)

            try:
                it.deal()
            except Exception as e:
                print(e)

            i = i+1
            if i % 5 == 0:
                print("已完成 %5d\t/ %5d" % (i, count))

        return


def main():
    info = SyncMethod.createLink()

    # 再次确认是否同步
    SyncMethod.show(info)

    print("-------------------------------------")
    input("回车开始分析，Ctrl+C 退出")

    action = SyncMethod.doAnalyse(info)

    print("-------------------------------------")
    if len(action) == 0:
        print("分析已完成，所有文件均为最新。。。回车退出")
        return

    print('分析已完成，即将做如下修改：')
    with open(log_file, 'w', encoding='utf-8') as f:
        for it in action:
            f.write(SyncStuct(it).show())

    if os.name == "nt":
        os.system("notepad "+log_file)
    else:
        os.system("vi "+log_file)

    choose = input("按 y 立即做如下修改，否则退出: ")
    if choose == "Y" or choose == "y":
        SyncMethod.doSync(action)
        print("修改已完成。。。。回车退出")

    return


if __name__ == '__main__':
    main()
    input("")
