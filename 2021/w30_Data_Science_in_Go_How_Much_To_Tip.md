## Data Science in Go: How Much To Tip
- 原文地址：https://www.ardanlabs.com/blog/2021/07/go-data-science-how-much-tip.html
- 原文作者：Miki Tebeka
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w11_Go_Developer_Survey_2020_Results.md
- 译者：[lsj1342](https://github.com/lsj1342)
- 校对：[]()
* * *
### The Question

When you work on data science problems, you always start with a question you’re trying to answer. This question will affect the data you pick, your exploration process, and how you interpret the results.

The question for this article is: How much (in percentage) should you tip your taxi driver?

To answer the question, we’ll use a portion of the [NYC Taxi dataset](https://www1.nyc.gov/site/tlc/about/tlc-trip-record-data.page). The data file we’ll be using is [taxi-01-2020-sample.csv.bz2](https://github.com/353words/taxi/raw/master/taxi-01-2020-sample.csv.bz2)

_Note: CSV is a horrible, horrible format. There’s no standard, no schema and everything is unmarshalled to text (unlike JSON where you have types). If you can, pick another format. My preferred data storage format is [SQLite](https://www.sqlite.org/)._

### Exploration Code

We’re searching for the answer to our question, we’ll be focused on productivity. If at some point this code will get to production, go ahead and refactor it.

To simplify working with the input, we’ll pass the input file in the standard input. We’ll have several stages of exploring the data and each will have a corresponding command line switch. In the `main` function we have the following line:

```
r := bzip2.NewReader(os.Stdin)
```

and then we’ll call each exploration step with `r`.

### First Contact

Before you start working with data, it’s important to have a quick look at it to see that it matches your expectations. You should also check that the data fits in memory.

**Listing 1: First Look**

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

Listing 1 shows the first look on the data. On line 21, we create a `bufio.Scanner` to scan line by line. On lines 23-25, we print the first 5 lines from the file. On line 34, we print the file size and on line 35, we print the number of lines.

**Listing 2: Running First Look**

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

Listing 2 shows how to run the first step. We run the program with `go run`. In the output we see the first 5 lines and the uncompressed file size and the number of lines.

The file is a CSV file and small enough to fit in memory. To calculate the tip percentage we need only two columns: `tip_amount` and `total_amount`. If you’re curious about the data schema, see [here](https://www1.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf).

### Loading the Data

Once the initial look aligns with your assumptions, you can load the data. We’re going to use `github.com/jszwec/csvutil` to parse the CSV and [gonum](https://www.gonum.org/) to calculate some statistics.

**Listing 3: Imports**

```
14     "github.com/jszwec/csvutil"
15     "gonum.org/v1/gonum/floats"
16     "gonum.org/v1/gonum/stat"
```

Listing 3 shows the external imports in our code. On line 14, we import `csvutil` and on lines 15-16, we import `floats` and `stat` from `gonum`.

**Listing 4: Load Data**

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

Listing 4 shows how we load the data. On lines 62-65, we define a `Row` struct with the fields that interest us. On line 68, we define the `tip` and `amount` slices to hold the values from the `tip_amount` and `total_amount` fields in the CSV. On lines 74-88, we run a `for` loop to upload the data and finally on line 90, we return the data.

**Listing 5: Statistics**

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

Listing 5 shows the `statistics` step of our data exploration. On line 40, we load the date. On lines 45-50, we print the minimal, mean (average) and maximal values for the tip. On lines 52-57, we do the same for the total.

**Listing 6: Running Statistics**

```
$ go run taxi.go -stats < taxi-01-2020-sample.csv.bz2 
tip: min=-11.80, mean=2.21, max=333.50
total: min=-333.30, mean=18.47, max=4268.30
```

Listing 6 shows how to run the statistics step. We can see there are some bad values. Both minimum values are negative and the maximal value for the total amount is more than $4,000.

In any real life dataset you will have bad values, and you need to decide what to do with them. We’re going to take the easy approach and ignore them. We will filter out negative values. Also, since we’re not planning on taxi rides that cost more than $100, we’ll filter out rows with `total_amount` bigger than 100.

### Tip

**Listing 7: Load Filtered Data**

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

Listing 7 shows loading of filtered data. The only difference from `loadData` are lines 133-135 where we filter out rows.

Now we can calculate the tip we want to pay. We’d like to be on the generous side so we’ll use the 75% [quantile](https://en.wikipedia.org/wiki/Quantile) value. The 75% quantile (or percentile) is a number that 75% of the values are below it.

**Listing 8: Desired Tip**

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

Listing 8 shows the `desiredTip` function. On line 94, we load the filtered data. On line 99, we print how many filtered values we have to check so we don’t filter out too many rows. On lines 101-104, we create a slice of percentages. Finally on lines 107-110, we calculate the 75% percentile and on line 107, we print it.

**Listing 9: Running Desired Tip**

```
$ go run taxi.go -tip < taxi-01-2020-sample.csv.bz2 
716422 filtered values
0.75 quantile tip: 0.20
```

Listing 9 shows the `tip` step output. We see we filtered out about 30% of the rows. And finally, we see that the 75% quantile is 20%.

But wait! Maybe we should tip more on the weekend? Let’s have a look:

**Listing 10: Loading Data With Time**

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

Listing 10 shows how to load the data with time. On lines 145-149, we write an `unmarshalTime` function to parse time from a `[]byte`. On lines 151-155, we define `TimeRow` which is a row that contains a `Time` field. On line 159, we define the `times` slice and on line 160, we register `unmarshalTime` to handle `time.Time` fields. Finally on line 187, we return the times, tip and total.

**Listing 11: Tip by Weekday**

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

Listing 11 shows the “tip by weekday” calculation. On line 196, we use a map to hold percentages per weekday. On lines 197 to 201, we populate the percentages for each week day, this is the equivalent of a “GROUP BY” operation in a database. On lines 203-209, we go over each weekday, calculate the .75 quantile and print it out.

On line 209, we use the `-10s%` verb to have all weekdays take at least 10 characters and aligned to the line. This might seem like a trivial detail, but aligned output is much easier to compare for us humans - as you can see in the output below. We also align the number of samples for the same reason.

**Listing 12: Running Weekday Tip**

```
$ go run taxi.go -daily < taxi-01-2020-sample.csv.bz2
Sunday    : 0.75 quantile tip: 0.20 ( 77942 samples)
Monday    : 0.75 quantile tip: 0.20 ( 82561 samples)
Tuesday   : 0.75 quantile tip: 0.20 ( 97634 samples)
Wednesday : 0.75 quantile tip: 0.20 (118497 samples)
Thursday  : 0.75 quantile tip: 0.20 (125692 samples)
Friday    : 0.75 quantile tip: 0.20 (125743 samples)
```

Listing 12 shows how to run the daily step. We can see that there’s no difference in the tip percentage over the weekend.

### Conclusion

A little curiosity and a little Go will get you pretty far in your data science journey. You don’t have to use deep learning, decision trees, support vector machines and other algorithms to get useful answers.

How are you using Go for data science? I’d love to hear, ping me at miki@ardanlabs.com.