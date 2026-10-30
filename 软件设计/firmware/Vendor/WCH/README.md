# WCH SDK来源

本目录选取自原厂仓库 https://github.com/openwch/ch32v003 ，固定提交：

`4e1b7437ada5d3ae8831a6f4b811a6320e4e23c7`

全部28个上游文件保持原字节内容，其路径和SHA-256见provenance.json。上游文件头的版权与使用条件保留：原厂软件及修改版/二进制用于南京沁恒微电子制造的MCU。项目目标为CH32V003F4P6。

实际构建只使用启动文件、Core头文件、Peripheral头文件和gpio/rcc/tim/iwdg/misc五个外设源文件。Core/core_riscv.c保留作上游参考，未加入当前构建。

Project目录中的派生文件单独修改：

- system_ch32v00x.c：启用24MHz HSI、关闭48MHz HSE默认配置；移除时钟初始化中对PD1的GPIO重配置，保留SWIO。
- system_ch32v00x.h：从相同提交复制，未改动。
- Link.ld：保持原厂Flash原点0x00000000和2KB SRAM；栈由256增至512字节，加入RAM与栈不重叠断言。

Project中的副本不冒充未修改的Vendor原件。构建清单记录全部工程源文件校验值。
