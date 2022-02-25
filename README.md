# translator

翻译小组文章


## 翻译指南

### 翻译步骤

1. 在 [issues](https://github.com/gocn/translator/issues) 提出待翻译的文章
2. 回复「认领翻译」开始翻译
3. 提 [pr](https://github.com/gocn/translator/pulls) 将原文转化为 Markdown 格式的文件，并将原文的图片等资源下载后存放在本项目的 `static` 目录，防止资源失效
4. markdown 的 pr 合并后，再提一个翻译的 pr

### 格式要求

* 请遵循 [中文文案排版指北](https://github.com/sparanoid/chinese-copywriting-guidelines/blob/master/README.zh-CN.md)
* 使用工具 [lint-md](https://github.com/hustcc/lint-md) 做自动检测

## 近期文章列表

### Go 官方文档与手册

- [Go 官方出品泛型教程：如何开始使用泛型](https://gocn.vip/topics/20885) （[zxmfke](https://github.com/zxmfke) 翻译）
- [Go 1.16 即将到来的函数：ReadDir 和 DirEntry](https://github.com/gocn/translator/blob/master/2021/w6_coming_in_go_1.16_readdir_and_direntry.md) ([cvley](https://github.com/cvley)  翻译)

### Go 新特性/发展

- [Go 快速指南：go1.18 特性](https://gocn.vip/topics/20849) （[cuua](https://github.com/cuua) 翻译）
- [Go 1.18 中即将出现的功能特性](https://gocn.vip/topics/17460) （[Cluas](https://github.com/Cluas) 翻译）
- [Go 1.16 新功能：Go Module 支持版本撤回](https://gocn.vip/topics/11667) （[咔叽咔叽](https://github.com/github.com/watermelo) 翻译）
- [Go 1.16 中 Module 功能新变化](https://github.com/gocn/translator/blob/master/2021/w8_New_module_changes_in_Go_1.16.md) (Jay Conrod 翻译)
- [2021 Go 趋势报告](https://gocn.vip/topics/11650)（[朱亚光](https://github.com/zhuyaguang) 翻译）
- [更多Go 新特性/发展 文章...](https://github.com/gocn/translator/blob/master/feature_and_future.md)

### Go 泛型

- [Go 1.18 泛型的一些技巧和困扰](https://gocn.vip/topics/17485) （[Cluas](https://github.com/Cluas) 翻译）
- [使用 Go 泛型的函数式编程](https://gocn.vip/topics/12233) （[cvley](https://github.com/github.com/cvley) 翻译）
- [泛型来了，看看如何应用到 slice](https://gocn.vip/topics/11725) （Jancd 翻译）
- [你想知道的 Go 泛型](https://github.com/gocn/translator/blob/master/2021/w13_Generics_in_Go.md)（[haoheipi](https://github.com/haoheipi) 翻译）

### Go 数据结构

- [Go 语言是如何计算 len() 的?](https://gocn.vip/topics/12437) （[twx](https://github.com/1-st) 翻译）
- [Go 如何知道 time.Now](https://github.com/gocn/translator/blob/master/2021/w14_how_does_go_know_time_now.md) ([cvley](https://github.com/cvley) 翻译)
- [Go sync map 的内部实现](https://github.com/gocn/translator/blob/master/2021/w29_Go%20Inside%20sync.Map%E2%80%8A%E2%80%94%E2%80%8AHow%20does%20sync.Map%20work%20internally.md) ([guzzsek](https://github.com/laxiaohong) 翻译)
- [sync.RWMutex - 解决并发读写问题](https://github.com/gocn/translator/blob/master/2019/w13_sync_mutex_translation.md) ([fivezh](https://github.com/fivezh) 翻译)
- [理解 Go 语言中的 defer](https://github.com/gocn/translator/blob/master/2019/w43_understanding_defer_in_go.md) ([lsj1342](https://github.com/lsj1342) 翻译)
- [上下文 Context 与结构体 Struct](https://gocn.vip/topics/11707)（Kevin 翻译）

### Go 并发

- [Go原生并发基本原理与最佳做法](https://gocn.vip/topics/21927) （[zxmfke](https://github.com/zxmfke) 翻译）
- [以 Go 为例-探究并行与并发的区别](https://gocn.vip/topics/20993) （[zxmfke](https://github.com/zxmfke) 翻译）
- [Go 高级并发](https://gocn.vip/topics/9883) ([咔叽咔叽](https://github.com/watermelo) 翻译)

### Go GC

- [golang 垃圾回收器如何标记内存？](https://gocn.vip/topics/12251) （[cuua](https://github.com/github.com/cuua) 翻译）

### Go 调度

- [Go 的抢占式调度](https://gocn.vip/topics/12062) （[lsj1342](https://github.com/lsj1342) 翻译）

### Go 内存管理

- [Golang 在大规模流处理场景下的最小化内存使用](https://gocn.vip/topics/20995) （[haoheipi](https://github.com/haoheipi) 翻译）
- [定位并修复 Go 中的内存泄漏](https://gocn.vip/topics/17437) （[Fivezh](https://github.com/fivezh) 翻译）
- [golang 逃逸分析](https://github.com/gocn/translator/blob/master/2021/w15_golang_escape_analysis.md) ([cuua](https://github.com/cuua) 翻译)
- [Go 内存管理概述](https://github.com/gocn/translator/blob/master/2021/w21_An_overview_of_memory_management_in_Go.md) ([haoheipi](https://github.com/github.com/haoheipi) 翻译)

### Go 性能优化

- [Go 中的阻塞分析](https://gocn.vip/topics/17448) （[lsj1342](https://github.com/lsj1342) 翻译）
- [Go 语言的 goroutine 性能分析](https://gocn.vip/topics/17418) （[朱亚光](https://github.com/zhuyaguang) 翻译）
- [Go 的栈追踪](https://gocn.vip/topics/17343) （[cuua](https://github.com/cuua) 翻译）
- [两次拷贝操作的故事](https://gocn.vip/topics/12465) （[haoheipi](https://github.com/haoheipi) 翻译）
- [pprof++: 一个带有硬件监控的 Go Profiler](https://github.com/gocn/translator/blob/master/2021/w20_pprof_go_profiler.md)  ([tt](https://github.com/github.com/1-st) 翻译)
- [更多Go 性能优化 文章...](https://github.com/gocn/translator/blob/master/performance.md)

### 错误处理

- [Golang 中高效的错误处理](https://gocn.vip/topics/21016) （[Cluas](https://github.com/Cluas) 翻译）

### Go 代码风格

- [Uber Go 语言代码风格指南](https://github.com/gocn/translator/blob/master/2019/w38_uber_go_style_guide.md) ([咔叽咔叽](https://github.com/watermelo) 翻译)
- [关于 Go 代码结构的思考](https://gocn.vip/topics/20960) （[lsj1342](https://github.com/lsj1342) 翻译）
- [以层的方式而不是组的方式进行包管理](https://gocn.vip/topics/11666)  ([cvley](https://github.com/github.com/cvley)翻译)
- [浅谈如何组织 Go 代码结构](https://github.com/gocn/translator/blob/master/2021/w20_Thoughts_on_how_to_structure_Go_code.md) ([Fivezh](https://github.com/github.com/fivezh) 翻译)
- [清晰胜过聪明](https://gocn.vip/topics/9604) ([咔叽咔叽](https://github.com/watermelo) 翻译)

### Go 测试

- [Go 模糊测试](https://gocn.vip/topics/20941) ([fivezh](https://github.com/fivezh) 翻译)

### Go 与其他语言比较

- [Rust 与 Go: 为何相得益彰](https://gocn.vip/topics/20929) （[xkkhy](https://github.com/github.com/xkkhy) 翻译）
- [何时使用 Rust, 何时使用 Go](https://github.com/gocn/translator/blob/master/2021/w12_When_to_use_Rust_and_when_to_use_Go.md)（[tt](https://github.com/1-st) 翻译）
- [选择技术栈](https://github.com/gocn/translator/blob/master/2019/w14_choosing_a_language_stack.md) ([louyuting](https://github.com/louyuyting) 翻译)
- [将 5 万行 Java 代码移植到 Go 学到的经验](https://gocn.vip/topics/9602) ([cvley](https://github.com/cvley) 翻译)

### Go 安全

- [手把手教你用 Go 实现一个 mTLS](https://gocn.vip/topics/17472) （[朱亚光](https://github.com/zhuyaguang) 翻译）
- [Go 安全性备忘单：Go 开发者的 8 个安全性最佳实践](https://github.com/gocn/translator/blob/master/2021/w10_Go_Security_cheatsheet.md)（[guzzsek](https://github.com/guzzsek) 翻译）
- [Go 语言命令行执行路径的安全性](https://gocn.vip/topics/11648) （[朱亚光](https://github.com/zhuyaguang) 翻译）

### GO 应用/实践

- [Uber 的 API 网关架构](https://github.com/gocn/translator/blob/master/2021/w22_uber_architecture_api_gateway.md) ([咔叽咔叽](https://github.com/github.com/watermeloooo) 翻译)
- [Go sync.Once 的妙用](https://gocn.vip/topics/12514) （[张宇](https://github.com/pseudoyu) 翻译）
- [用 golang 实现 Serverless 服务](https://github.com/gocn/translator/blob/master/2021/w26_How_I'm_writing_Serverless_Services_in_Golang_these_days.md) ([Jancd](https://github.com/Jancd) 翻译)
- [在 Go 程序中使用 context 提供的取消功能](https://github.com/gocn/translator/blob/master/2019/w13.md) ([yufeng0924](https://github.com/yufeng0924) 翻译)
- [如何使用 HTTP 中间件](https://gocn.vip/topics/9603) ([咔叽咔叽](https://github.com/watermelo) 翻译)
- [更多Go 应用/实践 文章...](https://github.com/gocn/translator/blob/master/practices.md)

### 其他

- [2021 年，Clickhouse 在日志存储与分析方面作为 ElasticSearch 和 MySQL 的替代方案](https://gocn.vip/topics/11814) （[Fivezh](https://github.com/fivezh) 翻译）
- [Pinterest 如何保障扩展 Kubernetes](https://github.com/gocn/translator/blob/master/2021/w27_scaling_k8s_with_assurance_at_pinterest_introduction.md) ([咔叽咔叽](https://github.com/github.com/watermeloooo)  翻译)
- [Kubernetes vs Docker:了解 2021 年的容器](https://github.com/gocn/translator/blob/master/2021/w3_kubernetes_vs_docker.md)  (zhangyang  翻译)
