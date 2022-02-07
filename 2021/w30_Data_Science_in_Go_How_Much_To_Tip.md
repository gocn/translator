## Go 应用于数据科学的案例分享：付多少小费
- 原文地址：https://www.ardanlabs.com/blog/2021/07/go-data-science-how-much-tip.html
- 原文作者：Miki Tebeka
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w30_Data_Science_in_Go_How_Much_To_Tip.md
- 译者：[lsj1342](https://github.com/lsj1342)
- 校对：[laxiaohong](https://github.com/laxiaohong)、[cvley](https://github.com/cvley)
* * *
### 提出问题

当处理数据科学难题时，你总会以一个你想要回答的问题开始。这个问题将会影响你选择数据，探索过程以及解释结果。

本文的问题是：你应该给出租车司机多少（按百分比）小费？

为了回答这个问题，我们将使用[纽约市出租车数据集](https://www1.nyc.gov/site/tlc/about/tlc-trip-record-data.page)的一部分，使用的数据文件是[taxi-01-2020-sample.csv.bz2](https://github.com/353words/taxi/raw/master/taxi-01-2020-sample.csv.bz2)

_注意： CSV 是一种十分令人讨厌的格式。它没有标准，没有模式，所有内容都被解释为文本（与 JSON 不同）。如果可以，请选择其他格式。我首选的数据存储格式是 SQLite 。_

### 探索过程的代码

我们正在寻找问题的答案，我们将专注于快速实现。如果以后将此代码投入到生产环境下，那么继续重构它。

为了简化输入的工作，我们将在标准输入中传递输入文件。我们将有几个探索数据的阶段，每个阶段都有一个相应的命令行开关。在 `main` 函数中，我们有以下行：

```
r := bzip2.NewReader(os.Stdin)
```

并且，我们在每个探索步骤都会调用到 `r` 。

### 初探

在开始处理数据之前，快速查看它是否符合你的期望。此外，你还应该检查数据是否适合放入内存。

**步骤 1：初次查看**

```
19 func firstLook(r io.Reader) error {
20     var numLines, numBytes int
21     s := bufio.NewScanner(r)
22     for s.Scan() {
23         if numLines < 5 {
24             fmt.Println(s.Text())
25         }
26         numBytes += len(s.Text())
27         numLines++
28     }
29 
30     if err := s.Err(); err != nil {
31         return err
32     }
33 
34     fmt.Printf("size: %.2fMB\n", float64(numBytes)/1_000_000)
35     fmt.Printf("lines: %d\n", numLines)
36     return nil
37 }
```

步骤 1 显示了对数据的初步了解。在第 21 行，我们创建了一个 bufio.Scanner 用以逐行扫描。在第 23-25 行，我们打印文件的前 5 行。在第 34 行，我们打印文件大小，在第 35 行，我们打印了行数。

**步骤 2: 运行代码**

```
$ go run taxi.go -first_look < taxi-01-2020-sample.csv.bz2
VendorID,tpep_pickup_datetime,tpep_dropoff_datetime,passenger_count,trip_distance,RatecodeID,store_and_fwd_flag,PULocationID,DOLocationID,payment_type,fare_amount,extra,mta_tax,tip_amount,tolls_amount,improvement_surcharge,total_amount,congestion_surcharge
2,2003-01-01 00:07:17,2003-01-01 14:16:59,1.0,0.0,1.0,N,193,193,2.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0
2,2008-12-31 23:35:00,2008-12-31 23:36:53,1.0,0.42,1.0,N,263,263,2.0,3.5,0.5,0.5,0.0,0.0,0.3,7.3,2.5
2,2009-01-01 00:06:19,2009-01-01 00:10:22,1.0,0.85,1.0,N,107,137,2.0,5.0,0.0,0.5,0.0,0.0,0.3,8.3,2.5
2,2009-01-01 00:48:28,2009-01-01 00:57:48,1.0,0.93,1.0,N,100,186,2.0,7.5,0.0,0.5,0.0,0.0,0.3,10.8,2.5
size: 101.68MB
lines: 1000001
```

步骤 2 展示了如何运行第一步。我们用 `go run` 来运行代码。在输出中，我们看到文件的前 5 行以及未压缩文件的大小和行数。

该文件是一个 CSV 文件，小到可以放入内存。要计算小费百分比，我们只需要两列：`tip_amount` 和 `total_amount`。如果您对数据模式感到好奇，请参阅[此处](https://www1.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf)。

### 加载数据

一旦初次查看的结果与您的假设一致，您就可以加载数据。我们将使用 `github.com/jszwec/csvutil` 解析 CSV 和 [gonum](https://www.gonum.org/) 来计算一些统计信息。

**步骤 3: 依赖引入**

```
14     "github.com/jszwec/csvutil"
15     "gonum.org/v1/gonum/floats"
16     "gonum.org/v1/gonum/stat"
```

步骤 3 展示了代码中的外部依赖导入。在第 14 行，我们导入 `csvutil` ，在第 15-16 行，我们从`gonum` 导入 `floats` 和 `stat`。

**步骤 4: 加载数据**

```
62 type Row struct {
63     Tip   float64 `csv:"tip_amount"`
64     Total float64 `csv:"total_amount"`
65 }
66 
67 func loadData(r io.Reader) ([]float64, []float64, error) {
68     var tip, total []float64
69     dec, err := csvutil.NewDecoder(csv.NewReader(r))
70     if err != nil {
71         return nil, nil, err
72     }
73 
74     for {
75         var row Row
76         err := dec.Decode(&row)
77 
78         if err == io.EOF {
79             break
80         }
81 
82         if err != nil {
83             return nil, nil, err
84         }
85 
86         tip = append(tip, row.Tip)
87         total = append(total, row.Total)
88     }
89 
90     return tip, total, nil
91 }
```

步骤 4 显示了我们如何加载数据。在第 62-65 行，我们定义了一个 `Row` 结构体来包含我们感兴趣的字段。在第 68 行，我们定义了 `tip` 和 `amount` 切片来保存 CSV 中 `tip_amount` 和 `total_amount` 字段的值。在第 74-88 行，我们运行一个 for 循环来上传数据。最后在第 90 行，进行数据返回。

**步骤 5: 统计**

```
39 func statistics(r io.Reader) error {
40     tip, total, err := loadData(r)
41     if err != nil {
42         return err
43     }
44 
45     fmt.Printf(
46         "tip: min=%.2f, mean=%.2f, max=%.2f\n",
47         floats.Min(tip),
48         stat.Mean(tip, nil),
49         floats.Max(tip),
50     )
51 
52     fmt.Printf(
53         "total: min=%.2f, mean=%.2f, max=%.2f\n",
54         floats.Min(total),
55         stat.Mean(total, nil),
56         floats.Max(total),
57     )
58 
59     return nil
60 }
```

步骤 5 显示了 statistics 我们数据探索的步骤。在第 40 行，我们加载日期。在第 45-50 行，我们打印了小费的最小值、平均值（平均值）和最大值。在第 52-57 行，我们对总数执行相同的操作。

**步骤 6: 运行统计代码**

```
$ go run taxi.go -stats < taxi-01-2020-sample.csv.bz2 
tip: min=-11.80, mean=2.21, max=333.50
total: min=-333.30, mean=18.47, max=4268.30
```

步骤 6 显示了如何运行统计步骤的代码。我们可以看到有一些不好的值。两个最小值都是负数并且总金额的最大值超过 4,000 美元。

在任何现实生活中的数据集中，都会有错误的值，你需要决定如何处理它们。我们将采用简单的方法并忽略它们。我们将过滤掉负值。此外，由于我们不打算乘坐费用超过 100 美元的出租车，因此我们将过滤掉 `total_amount` 大于 100 的行。

### 小费计算

**步骤 7: 加载过滤数据**

```
114 func loadDataFiltered(r io.Reader) ([]float64, []float64, error) {
115     var tip, total []float64
116     dec, err := csvutil.NewDecoder(csv.NewReader(r))
117     if err != nil {
118         return nil, nil, err
119     }
120 
121     for {
122         var row Row
123 
124         err := dec.Decode(&row)
125         if err == io.EOF {
126             break
127         }
128 
129         if err != nil {
130             return nil, nil, err
131         }
132 
133         if row.Total <= 0 || row.Tip <= 0 || row.Total > 100 {
134             continue
135         }
136 
137         tip = append(tip, row.Tip)
138         total = append(total, row.Total)
139     }
140 
141     return tip, total, nil
142 }
```

步骤 7 展示了对过滤数据的加载。和 `loadData` 唯一的区别是第 133-135 行的过滤操作。

现在我们可以计算我们想要支付的小费。我们希望保持慷慨，因此我们将使用 75% 的[分位数值](https://en.wikipedia.org/wiki/Quantile)。75% 分位数（或百分位数）是 75% 的值低于它的数字。

**步骤 8: 期待支出的小费**

```
93  func desiredTip(r io.Reader) error {
94      tip, total, err := loadDataFiltered(r)
95      if err != nil {
96          return err
97      }
98  
99      fmt.Printf("%d filtered values\n", len(tip))
100 
101     pct := make([]float64, len(tip))
102     for i, t := range tip {
103         pct[i] = t / (total[i] - t)
104     }
105 
106     // stat.Quantile required sorted values
107     sort.Float64s(pct)
108     q := 0.75
109     val := stat.Quantile(q, stat.Empirical, pct, nil)
110     fmt.Printf("%.2f quantile tip: %.2f\n", q, val)
111     return nil
112 }
```

步骤 8 展示了 `desiredTip` 函数。在第 94 行，我们加载了过滤后的数据。在第 99 行，我们打印了过滤后的行数，这样方便我们检查不会过滤掉太多行。在第 101-104 行，我们创建了一个百分比切片。最后在第 107-110 行，我们计算 75% 的百分位数，并在第 110 行，我们把它打印了出来。

**步骤 9: 运行代码**

```
$ go run taxi.go -tip < taxi-01-2020-sample.csv.bz2 
716422 filtered values
0.75 quantile tip: 0.20
```

步骤 9 展示了 `tip` 步骤输出。我们看到我们过滤掉了大约 30% 的行。最后，我们看到 75% 的分位数是 20%。

可是，等等！也许我们会在周末多给点小费？我们来看一下：

**步骤 10: 加载携带时间的数据**

```
145 func unmarshalTime(data []byte, t *time.Time) error {
146     var err error
147     *t, err = time.Parse("2006-01-02 15:04:05", string(data))
148     return err
149 }
150 
151 type TimeRow struct {
152     Tip   float64   `csv:"tip_amount"`
153     Total float64   `csv:"total_amount"`
154     Time  time.Time `csv:"tpep_pickup_datetime"`
155 }
156 
157 func loadDataWithTime(r io.Reader) ([]time.Time, []float64, []float64, error) {
158     var tip, total []float64
159     var times []time.Time
160     dec, err := csvutil.NewDecoder(csv.NewReader(r))
161     dec.Register(unmarshalTime)
162     if err != nil {
163         return nil, nil, nil, err
164     }
165 
166     for {
167         var row TimeRow
168 
169         err := dec.Decode(&row)
170         if err == io.EOF {
171             break
172         }
173 
174         if err != nil {
175             return nil, nil, nil, err
176         }
177 
178         if row.Total <= 0 || row.Tip <= 0 || row.Total > 100 {
179             continue
180         }
181 
182         tip = append(tip, row.Tip)
183         total = append(total, row.Total)
184         times = append(times, row.Time)
185     }
186 
187     return times, tip, total, nil
188 }
```

步骤 10 显示了如何加载数据的时间维度。在第 145-149 行，我们编写了一个 `unmarshalTime` 函数来从 `[]byte` 解析为时间。在第 151-155 行，我们定义 `TimeRow` 为包含 `Time` 字段的行。在第 159 行，我们定义了 `times` 切片，在第 160 行，我们注册 `unmarshalTime` 以处理 `time.Time` 字段。最后在第 187 行，我们返回时间、小费和总数。

**步骤 11: 按工作日计算小费**

```
190 func weekdayTip(r io.Reader) error {
191     times, tip, total, err := loadDataWithTime(r)
192     if err != nil {
193         return err
194     }
195 
196     pct := make(map[time.Weekday][]float64)
197     for i, t := range tip {
198         wday := times[i].Weekday()
199         p := t / (total[i] - t)
200         pct[wday] = append(pct[wday], p)
201     }
202 
203     for wday := time.Sunday; wday < time.Saturday; wday += 1 {
204         // stat.Quantile required sorted values
205         p := pct[wday]
206         sort.Float64s(p)
207         q := 0.75
208         val := stat.Quantile(q, stat.Empirical, p, nil)
209         fmt.Printf("%-10s: %.2f quantile tip: %.2f (%6d samples)\n", wday, q, val, len(p))
210     }
211 
212     return nil
213 }
```

步骤 11 展示了 “工作日小费” 计算。在第 196 行，我们使用字典来保存每个工作日的百分比。在第 197 到 201 行，我们填充每个工作日的百分比，这相当于数据库中的 “GROUP BY” 操作。在第 203-209 行，我们遍历每个工作日，计算 0.75 分位数并将其打印出来。

在第 209 行，我们使用 `-10s%` 让所有工作日至少占 10 个字符来行对齐。这似乎是一个微不足道的细节，但对齐输出对于我们来说会更容易比较 - 正如您在下面的输出中看到的那样。出于同样的原因，我们也对齐了样本数量。

**步骤 12: 运行代码**

```
$ go run taxi.go -daily < taxi-01-2020-sample.csv.bz2
Sunday    : 0.75 quantile tip: 0.20 ( 77942 samples)
Monday    : 0.75 quantile tip: 0.20 ( 82561 samples)
Tuesday   : 0.75 quantile tip: 0.20 ( 97634 samples)
Wednesday : 0.75 quantile tip: 0.20 (118497 samples)
Thursday  : 0.75 quantile tip: 0.20 (125692 samples)
Friday    : 0.75 quantile tip: 0.20 (125743 samples)
```

步骤 12 运行了上步骤的代码，展示了每天的数据结果。我们可以看到周末小费的百分比并没有差异。

### 结论

只需要一点好奇心并会一点 Go 就可以让您在数据科学之旅中走得更远。您不必使用深度学习、决策树、支持向量机和其他算法来获得有用的答案。

您正如何将 Go 用于数据科学？我很想听听，请通过 miki@ardanlabs.com 联系我。
