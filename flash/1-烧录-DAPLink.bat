@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "OCD=tools\xpack-openocd-0.12.0-7\bin\openocd.exe"
set "HEX=imu_to_dxl-0.2.0-feetech.hex"

echo ============================================================
echo  imu_to_dxl 0.2.0 (Feetech SCS/STS, ID 200) flash
echo  Probe: CMSIS-DAP / DAPLink   Target: STM32G031F8P6
echo ============================================================
echo Wiring: J2-2=SWCLK  J2-3=SWDIO  J2-4=GND  J2-1(3V3)=VTref
echo Board powered by 5V on J1-2 (VBATT). See README.md first!
echo ------------------------------------------------------------
"%OCD%" -f interface/cmsis-dap.cfg -c "adapter speed 200" -f target/stm32g0x.cfg -c "init" -c "reset halt" -c "program %HEX% verify" -c "reset run" -c "shutdown"
echo ------------------------------------------------------------
if %ERRORLEVEL%==0 (
    echo [OK] Program + verify PASS.
    echo       NOW power-cycle the board once ^(off, then on^)!
) else (
    echo [FAIL] See messages above. Check wiring / driver / README.
)
pause
