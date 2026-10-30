# 键鼠共享器固件 v0.1.1

适用已投板的2026-10-21下午版：CH32V003F4P6、CH444G、CH334P，四个按键、四个指示灯、三个USB-A和一个下游USB-C。

已实现四键选择、20ms消抖、多键锁定、长按不连发、上电默认电脑4、先断后接、同目标保持连接，以及DEV/RELEASE看门狗策略。USB数据和新增Type-C由硬件处理，MCU不运行USB协议栈。

本版已通过电脑端实际C代码测试并完成交叉编译，**尚未上板验证**。

- [首次编译与烧录](02_编译与烧录.md)
- [测试与构建结果](03_测试与构建记录.md)
- [软件方案S1.0](01_软件方案.md)
- [应用源码入口](firmware/App/main.c)
- [样板验证包说明](releases/v0.1.1/README.md)

## 三种固件

| 文件 | 用途 | USB数据 | 看门狗 |
| --- | --- | --- | --- |
| simplekvm_bringup.hex | 首次检查四键四灯 | 始终断开 | 关闭 |
| simplekvm_dev.hex | 首次完整功能联调 | 正常按键切换 | 关闭 |
| simplekvm_release.hex | 长期运行配置的样板验证 | 正常按键切换 | 启用，目标约1秒 |

“release”是构建配置名称，不表示实板验收或量产放行。第一次验证USB功能使用dev；只检查按键和LED时使用bringup。

当前采用Python命令行构建工程，使用MounRiver专用GNU编译器；不依赖IDE安装。本次没有生成或验证MounRiver专用.wvproj文件，也不把普通文本冒充该工程格式。firmware/Makefile为可选构建入口。

## 快速构建

在本目录使用Python 3.9及以上：

```powershell
python tools/bootstrap_tools.py
python tests/test_behavior.py
python tools/build.py --profile all
```

工具便携下载到临时目录的英文路径，不改系统PATH，不安装IDE。已有MounRiver编译器可跳过下载，用`--gcc`指定riscv-none-embed-gcc.exe，或设置KVM_GCC。电脑端测试可用`--cc`指定Windows TinyCC；已安装支持Windows x64目标的完整Clang也可使用`--clang`。

本机具体路径只保存在tools/local_config.json，交付源码包不携带本机路径配置。详细版本、来源和复现方式见烧录文档。
