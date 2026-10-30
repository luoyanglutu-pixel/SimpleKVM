# SimpleKVM 4-PC USB Keyboard/Mouse Switch

SimpleKVM connects up to four computers to one group of USB keyboard/mouse peripherals. A CH444G selects one upstream USB data pair, a CH334P provides four downstream ports, and a CH32V003 controls the buttons, LEDs, and break-before-make timing.

The current v0.1.1 firmware defaults to PC4/LED4. The device switches USB data only; it does not switch video. Native Bluetooth peripherals are not supported unless they use a USB receiver.

This is a prototype release. An editable EasyEDA Pro `.epro2` project containing the schematic and PCB, plus the 2026-10-29 schematic PDF and BOM, firmware, SolidWorks files, STL, and 3MF files are included. A matching exported netlist, Gerbers, drill files, and placement files are still missing, so production files must be regenerated and reviewed before fabrication.

All five prototype boards are now functional. Three earlier failures were traced to damaged/high-resistance 0603 resettable fuses after the reflow process; replacing the fuses restored operation. This points to a part/profile/process qualification issue, not a general claim that resettable fuses cannot be reflow soldered.

See [README.md](README.md) for the complete Chinese documentation and the current prototype test status.

Licensing is split by content: custom firmware under MIT, custom electronic/mechanical hardware under CERN-OHL-P-2.0, documentation under CC BY-SA 4.0, and WCH SDK files under their original vendor terms.

