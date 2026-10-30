# GitHub发布说明

## 建议仓库信息

- Repository name：`SimpleKVM`
- Description：`Open-source 4-PC USB keyboard/mouse switch based on CH32V003, CH444G and CH334P.`
- Topics：`usb`、`kvm-switch`、`ch32v003`、`wch`、`usb-hub`、`hardware`、`3d-printing`
- 首个Release：`v0.1.1-prototype`

## 上传建议

1. 将`开源发布/SimpleKVM`作为Git仓库根目录。
2. 首次提交前检查`LICENSE.md`和`NOTICE.md`中的署名是否符合发布者要求。
3. 不要提交`软件设计/tools/local_config.json`、构建目录或临时工具链。
4. SolidWorks和3MF属于二进制文件；当前总量可直接提交。如后续文件明显增大，可启用Git LFS。
5. 在Release中附加`软件设计/releases/simplekvm_firmware_v0.1.1.zip`。
6. 在仓库About和README中明确“已提供EasyEDA Pro工程、Gerber/钻孔/坐标尚缺失”和“prototype”状态。

## 推荐提交顺序

```text
docs: add project overview and license matrix
hardware: publish audited schematic, BOM and netlist baseline
firmware: publish v0.1.1 source, tests and binaries
mechanical: publish SolidWorks, STL and 3MF files
docs: add JLCPCB and GitHub publishing notes
```

## 不建议现在宣称

- 不要写“可直接量产”。
- 不要写“USB 2.0认证通过”。
- 不要写“ESD保护完善”。
- 可以说明“5块样机已恢复基本功能”，但不要扩大为所有电脑、键鼠、热插拔、ESD/EMC和长期稳定性均验证通过。
- Gerber、钻孔和坐标未补齐前，不要写“可直接下单的完整生产资料”。

