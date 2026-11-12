# iQOO Neo9 兼容性核对

**状态：Shark 尚不支持本机 Neo9 内核；本目录提供只读检查，不提供提权实现。**

## 本机信息

2026-11-12 从设备读取：

| 项目 | 值 |
| --- | --- |
| 型号 | vivo V2338A / PD2338（iQOO Neo9） |
| Android | 16 |
| 系统版本 | PD2338B_A_16.2.13.2.W10 |
| 安全补丁日期 | 2026-07-01 |
| 完整内核版本 | `5.15.197-g708015331567-dirty` |
| ABI | arm64-v8a |

系统版本、安全补丁日期和内核版本不能单独证明某个漏洞是否存在，厂商可能回移修复。

## Timer 参考的核对结果

本机 `Timer-1.2.0-release.apk` 的包名为 `com.timer.cve98260`，版本号为
`1.2.0`（versionCode 4）。其文件列表包含：

```text
assets/kernel_profiles/5.15.197-g708015331567-dirty.conf
```

这证明该 APK 包含与本机内核同名的配置文件，不能据此确认配置正确、提权成功率，
或判断它能直接用于 Shark。本次仅检查 APK 元数据和配置文件的匹配情况，未运行
Timer、Shark 的提权程序或加载内核模块，也未复制 Timer 的配置参数及二进制。

## 与上游的差异

核对上游提交 `5e4d5bcf43de3d1db47d8e29b2b1715d6e577cb9`：

- App 的 `PROFILE_BY_RELEASE` 没有本机内核版本。
- 上游 runner 覆盖 6.6、6.12、6.18，没有 5.15 入口。
- 现有模块流程不能仅凭 Android 主版本判断为适用于本机。

因此，本 fork 保留上游的未支持判定；不会将 Neo9 映射到其他内核的 runner。

## 只读检查

在 Neo9 的 Termux 中，从仓库根目录运行：

```sh
python ports/neo9/check_compatibility.py
```

如需同时核对已有的 Timer APK：

```sh
python ports/neo9/check_compatibility.py \
  --timer-apk /sdcard/Download/Timer-1.2.0-release.apk
```

脚本只读取设备属性、当前源码的内核映射和指定 APK 的匹配配置；输出 JSON 到
标准输出。它不调用 adb、su、Shizuku 或 runner，不修改系统设置，也不连接网络。
输出中的 `shark_profile_match` 仅表示 App 源码包含对应映射，不表示真机验证通过。
