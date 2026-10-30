# Third-party notices

## WCH CH32V003 SDK

`软件设计/firmware/Vendor/WCH/`来自：

- Repository: https://github.com/openwch/ch32v003
- Pinned commit: `4e1b7437ada5d3ae8831a6f4b811a6320e4e23c7`

这些文件保留南京沁恒微电子的原始版权头。原始文件头规定：软件及其修改版/二进制用于南京沁恒微电子制造的微控制器。它们不属于本项目MIT授权范围。

`软件设计/firmware/Project/system_ch32v00x.c`及相关派生文件基于同一SDK修改，仍受原厂条件约束；修改内容和上游文件哈希记录在`软件设计/firmware/Vendor/WCH/README.md`和`provenance.json`。

## Electronic component models

`结构设计`中的部分连接器、封装和元件三维模型来自EDA库或器件供应方。项目只为装配参考而保留这些文件，不主张其版权，也不将其重新许可为CERN-OHL-P-2.0。

## Datasheets

本开源包没有重新分发芯片数据手册。请从WCH及相应器件厂商官网下载最新版本。

## Toolchains

本包不包含MounRiver GCC、TinyCC或其它编译器二进制。`bootstrap_tools.py`仅用于获取构建依赖；使用者应自行遵守各工具链许可。

