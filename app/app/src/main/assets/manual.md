# Shark 使用手册

Shark 通过 Stellar 或 Shizuku 以 shell 身份驱动设备端 98260 exploit，加载管理器 LKM。首次使用先完成授权，再一键越狱。

> Shark 目前支持 5.15.197、6.18.21、6.12.69、6.12.38、6.12.58、6.12.23、6.6.118 与 6.6.127 内核的欧加系 / vivo / iQOO 设备，按完整 `uname -r` 精确匹配；未匹配的机型会提示不支持。

## 快速开始

1. 先安装所选 ROOT 管理器（KernelSU / FinaSU / KernelSU Next / BakaSU / SukiSU Ultra），**暂不支持ci版本的 KernelSU Next**。
2. 启动并使用**无线调试或者adb**激活 **Stellar（推荐）** 或 **Shizuku** 服务，并授予 Shark 权限。
3. 回到 Shark 首页点「一键越狱」，等待成功日志；以 `DONE`、`SU_ID_RC=0` 和 `uid=0(root)` 为准。
4. 成功后管理器会自动拉起；开启对应开关时还会停用安全弹窗、加载 **SUSFS**（6.18/6.12 线；6.12 使用 `libsusfs_guard_lkm_612.so`）或 **VFS**（仅 6.18.21）。
5. 若日志显示 **MODULE NOT LOADED**，无需重启设备，直接再次尝试越狱即可。
6. 每次进入 App 会自动检查更新：Gitee Releases 优先，GitHub 兜底；发现新版本会弹窗，可直接下载并交给系统安装器。也可在「关于」页手动点「检查更新」。

## 权限与准备

- **Stellar 优先、Shizuku 兜底**：两者都在时用 Stellar，Stellar 不可用才回落到 Shizuku。
- **管理器必须先安装**：ksud 不随包内置，运行时从管理器 APK 的 `lib/arm64` 原地执行。
- **建议在干净开机后执行**；5.15.197、6.18.21、6.12.69、6.12.38、6.12.58、6.12.23、6.6.118、6.6.127 各是独立入口，App 按完整 `uname -r` 精确选择。

## 一键越狱流程

**preflight**（内核 release / trace 通道）→ **98260 UAF**（fake cred / SELinux 零写）→ **cred 子进程一次性 ksud late-load** → 等模块与 su → **收尾**（ksud install、卸内核防护、SUSFS、VFS、截图恢复、拉起管理器）。

每个内核版本有独立的 K 源文件和 `libk<版本>.so`；无源码级复用，共享引擎在 `plant_core.inc`。vivo 机型（5.15.197 / 6.12.23 / 6.12.58 vivo 构建 / 6.6.127）会在唤醒 root 子进程前清零 `vr.ko` 使用的 tracepoint funcs 槽位；6.6.127 同时清零 `sched_process_exit` 槽位。6.12.58 OS7（`gdd6fd5c98918`）与 6.6.127 还要走 `hooks_defend` 加载门旁路：定位模块、一次零写解锁、发布 khs 白名单后再在进程内加载 KO。

- **快路径** plant 约 2–3 秒、全流程约 4–9 秒；回收未命中时会多花几秒，属正常波动。
- **任一链失败后**：plant 持有的页会转交给 holder，同一 boot 可直接再点一次；不要手工 kill 或 reap holder。

## 功能说明

- **首页**：ROOT 管理器下拉、流程开关（VFS 仅 6.18 显示；vivo V2505A / iQOO Neo9 5.15.197 隐藏反 root 三项；5.15.197 / 6.6.118 / 6.6.127 不显示 SUSFS/VFS/热切换；6.12.58 OS7 暂不显示 SUSFS，热切换保留）；信息卡显示内核版本与自动选择的漏洞利用方式。
- **日志**：本次运行的实时流式日志。
- **历史**：每次运行保存一个 `.log`；点开看全文，左滑条目露出「导出」按钮，可分享给其他应用。
- **关于**：版本号、检查更新、源代码 / 加入社区 / 问题反馈入口，以及由 AboutLibraries 生成的依赖清单（按库显示版本与许可证，点开可看详情）和随 APK 离线内置的开源许可全文（GPL-3.0、NOTICE、Apache-2.0、MIT、GPL-2.0、MPL-2.0）。
- **拓展功能 → Droidspaces 支持**（仅 6.18.21）：点「下载模块」会获取 GitHub 上 `Droidspaces-LKM` 的最新 release，确认后下载模块 zip；文件保存到 `Download/Shark/`，之后到 KernelSU 管理器「模块 → 安装」选择该文件刷入。模块不内置在 APK 中。
- **ROOT 管理器 → Dynamic Switching**（6.18.21 / 6.12.69 / 6.12.38 / 6.12.58 / 6.12.23；6.6.118 不支持）：选中后首次干净 boot 运行一次，由 `libksud_universal.so` 加载通用 KSU LKM（初始 KernelSU，内嵌 6.18/6.12 双 KMI KO）。加载后拓展功能出现「管理器热切换」项，可在 KernelSU / KernelSU-Next / BakaSU / SukiSU / FinaSU 间切换，无需重启或重新越狱；切换后重新打开目标管理器 App。

## 异常处理

| 日志 | 处理动作 |
| --- | --- |
| `PROBE_FAIL` / `kernel mismatch` | 当前内核不在支持列表（只按精确 `uname -r` 匹配已支持的 5.15.197 / 6.18.21 / 6.12.69 / 6.12.38 / 6.12.58 / 6.12.23 / 6.6.118 / 6.6.127）。 |
| `MANAGER` / `KSUD_MISSING` | 先安装对应的管理器 APK 再运行。 |
| `STALE_PLANT` | 上一轮 plant 仍在运行；等它转成 holder 后重试。 |
| `PLANT_FAIL` | plant 会保留 holder 并退出，同一 boot 可直接重试。 |
| `LATE_LOAD_FAIL` | 模块未在限定时间内出现；查看日志里的 ksud 输出，确认管理器版本匹配后直接重试。 |
| 内核崩溃/重启 | 属 98260 竞态固有风险，重启后再跑。 |

## 运行方式

- **6.18.21** → `libk61821.so`；**6.12.69** → `libk61269.so`（两个 OTA 构建按 uname 选调用点）。
- **6.12.38（PLR110）** → `libk61238.so`；**6.12.58（PLZ110 / V2505A OS6/OS7）** → `libk61258.so`；**6.12.23（V2505A）** → `libk61223.so`。
- **6.6.118（PKJ110 / PKH110 / Pad 等）** → `libk66118.so`（两个 OTA 构建按 uname 选调用点）；KMI android15-6.6。
- **6.6.127（vivo X200 Ultra / PD2454）** → `libk66127.so`；KMI android15-6.6，使用 vivo hooks_defend 加载门旁路。
- **5.15.197（iQOO Neo9 / PD2338）** → `libk515197.so`；KMI android13-5.15，清零 `__tracepoint_sys_exit->funcs`，不启用 SUSFS/热切换。
- 以上全部按**精确 `uname -r`** 匹配；未匹配时点击「一键越狱」直接提示机型不受支持。
- 所有入口都直接以 App 原生库（`nativeLibraryDir`）原地运行，子进程 cwd/HOME/TMPDIR 都在 App filesDir，不向 `/data/local/tmp` 部署工具或写文件；ksud 也从已安装的管理器 APK 原地执行。SUSFS 对 6.18/6.12 线支持（6.12 使用 `libsusfs_guard_lkm_612.so`），5.15.197 / 6.6.118 / 6.6.127 与 6.12.58 OS7 暂不支持；VFS 开关仅对 6.18 入口开放。
- 仅用于自有设备的系统研究。
