# SimpleKVM v0.1.1 样板验证包

硬件：2026-10-21下午版，CH32V003F4P6 + CH444G + CH334P。
电脑端23项实际C逻辑测试和三种交叉编译已通过；尚未上板验收。

## 先选文件

- bringup/simplekvm_bringup.hex：四键四灯检查，USB数据始终断开，看门狗关闭。全部释放后逐键按下才亮灯。
- dev/simplekvm_dev.hex：首次完整功能联调。默认电脑4，20ms消抖，先断后接，看门狗关闭。
- release/simplekvm_release.hex：相同功能，加约1秒目标超时看门狗；配置名称不表示量产放行。

首次USB功能联调选择dev，不要把bringup无法枚举误判为坏板。

## 烧录

WCH-LinkE，RISC-V/SDI模式。本板自供电，H1：1 SWIO、2 NRST、3 GND；下载器5V/3V3和SWCLK不接。
优先载入HEX，选CH32V003，编程并校验后复位。HEX携带地址，ELF链接原点为0x00000000；不要套用其它芯片BIN地址。
按键只改变数据通路；LED代表已选通道，不能确认主机在线或枚举完成。

开源发布目录仅保留HEX和BIN，避免公开带本机绝对路径的构建日志与调试文件。完整源码位于本仓库`软件设计/firmware`，上板步骤与未测项目见`软件设计/02_编译与烧录.md`和`03_测试与构建记录.md`。

`SHA256SUMS.txt`覆盖本目录公开文件。
