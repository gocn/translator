- 原文地址：[https://medium.com/@opheliaandcat/top-3-design-patterns-for-a-large-go-codebase-79a324003b47](https://www.featurebase.com/blog/range-encoded-bitmaps)
- 原文作者：
- 本文永久链接：
- 译者：[784909593](https://github.com/784909593)
- 校对：[zxmfke](https://github.com/zxmfke)

# 使用位图进行范围查询

FeatureBase 将整型数值存储在二进制, 范围编码（Range-Encoded）, 位切片索引（Bit-sliced Indexes）中，这篇博客分析了全部的实现。

## 引言

FeatureBase 是围绕着将所有内容表示为 bitmap 的概念构建的。对象之间的联系，例如，被视为 bool 值-关系存在或不存在-这些 bool 值的集合被存储为一系列 0 和 1。这些 bool 集合是 bitmaps，通过不同的按位运算使用 bitmaps，我们能非常快速的执行复杂查询。此外，bitmap 压缩技术使我们能够以非常紧凑的格式表示大量数据，从而减少了存储数据和执行查询所需的资源量。

使用 bitmaps 和[**Roaring bitmap compression**](http://roaringbitmap.org/), FeatureBase 非常擅长对数十亿个对象执行分割查询。但我们经常看到使用整数值会很有用的用例。例如，我们可能希望执行一个排除 foo 值大于 1000 的所有记录的查询。这篇文章逐步解释了我们如何将范围编码 bitmap 添加到 FeatureBase 中，使我们能够在查询操作中支持整数值。


这篇文章中描述的所有概念都是基于一些非常聪明的人在过去几十年中所做的研究。这是我试图在更高的层面来描述事情，但我鼓励你更多地阅读[**Bit-sliced Indexes**](https://cs.brown.edu/courses/cs227/archives/2008/Papers/Indexing/buchmann98.pdf)和[**Range-Encoding**](https://link.springer.com/chapter/10.1007/3-540-45675-9_8)。

## Bitmap 编码

首先，让我们假设我们想对[**动物王国**](https://en.wikipedia.org/wiki/Animal)的每个成员进行编目以这样一种方式，我们可以轻松有效地根据他们的特征来探索各种各样的各种物种。因为我们谈论的是 bitmap，所以示例数据集可能如下所示：:

![](https://uploads-ssl.webflow.com/62fe6fb36d2e0b5c203ee7c3/6324da7c6c247880c5d445c8_example-dataset.png)

_示例数据集_

### 相等编码位图

上面的例子显示了一组相等编码的位图，其中每行每个特征都是一个位图，指示哪些动物具有该特征。尽管这是一个相当简单的概念，但相等编码可能非常强大。因为它允许我们将一切表示为 bool 关系（即海牛有翅膀：是/否），所以我们可以对数据执行各种按位操作。

下一张图显示了我们如何通过对无脊椎动物和呼吸空气位图执行逻辑 AND 来找到所有呼吸空气的无脊椎动物。根据我们的样本数据，我们可以看到香蕉蛞蝓、花园蜗牛和车轮虫都具有这两种特征。

![](https://uploads-ssl.webflow.com/62fe6fb36d2e0b5c203ee7c3/6324db407737a6e77466c3df_bitwise-intersection.png)

_两个特征的逐位交集_

使用相等编码的位图可以取得很大进展，但 bool 值不能最好地表示原始数据的情况如何。如果我们想添加一个名为“圈养”的特征，它表示当前圈养的标本总数，并且我们想执行根据这些值筛选的查询，该怎么办？（正如您可能怀疑的那样，我们在以下示例中的 Captivity 的值完全是虚构的，但它们有助于演示这些概念。）

鉴于我们对相等编码位图的了解，我们可以采取几种（公认的幼稚）方法。一种方法是为每个可能的 Captivity 值创建一个特征（位图），如下所示：

![](https://uploads-ssl.webflow.com/62fe6fb36d2e0b5c203ee7c3/6324dbd07da3766796b2131f_captive-rows.png)

_Captivity 计数表示为单个位图_

这种方法是可以的，但它有几个局限性。首先，它的效率不是很高。根据基数的不同，您可能需要创建大量位图来表示所有可能的值。其次，如果您想按 Captivity 值的范围筛选查询，则必须对范围内的每个可能值执行 OR 运算。为了知道样本里哪些动物的 Captivity 值少于100个，您的查询需要执行以下操作：（Captivity=99或Captivity=98或Captivity=97或…）。你明白了。

另一种方法是创建 Captivity 范围的存储桶，而不是将每个可能的值表示为唯一的位图。在这种情况下，您可能会遇到这样的情况：

![](https://uploads-ssl.webflow.com/62fe6fb36d2e0b5c203ee7c3/6324dc5e68b86b2bfc081f29_captive-buckets.png)

_Captivity 计数（以桶表示）_

这种方法的一个好处是效率更高。查询也更容易，因为不必构造多个位图的并集来表示范围值。不利的一面是它没有那么细；通过将 47 转换为桶 0-99，您正在丢失信息。

这两种方法中的任何一种都是某些问题的完全有效的解决方案，但对于基数极高且信息丢失是不可接受的情况，我们需要另一种方法来表示非布尔值。我们需要这样做，即我们可以对值的范围执行查询，而无需编写真正庞大而繁琐的 OR 运算。为此，让我们讨论一下范围编码位图，以及它们如何避免我们在以前的方法中遇到的一些问题。

### 范围编码位图

首先，让我们以上面的例子为例，看看如果使用范围编码位图会是什么样子。

![](https://uploads-ssl.webflow.com/62fe6fb36d2e0b5c203ee7c3/6324dc8ccc7642f999bc5374_captive-range-encoded-rows.png)

_Captivity 计数用范围编码位图_

用范围编码位图表示一个值与我们使用相等编码所做的类似，但我们不只是设置与特定值对应的位，而是为每个大于实际值的值设置一个位。例如，因为有14只考拉熊的圈养（captivity），我们在位图 14 以及位图 15、16、17 等中设置了 bit。位图现在表示的不是具有特定圈养数量的所有动物的位图，而是具有并包括该数量的圈养数量的全部动物的位图。

这种编码方法使我们能够执行以前所做的范围查询，但我们可以从一个或两个位图中获得所需的内容，而不是对许多不同的位图执行 OR 运算。
例如，如果我们想知道哪些动物圈养的标本少于 15 个，我们只需提取 14 位图就可以了。如果我们想知道哪些动物的圈养标本超过 15 个，这有点复杂，但并不多。为此，我们提取表示最大计数的位图（在我们的情况下是 956 位图），然后减去 15 位图。

这些操作比我们以前的方法简单得多，效率也高得多。我们已经解决了为了找到我们的范围而将数十个位图进行 OR 运算的问题，并且我们不会像在桶方法中那样丢失任何信息。但我们仍然有几个问题使这种方法不太理想。首先，我们仍然需要保留一个位图来表示每一个特定的圈养数量。除此之外，我们还增加了复杂性和开销，不仅要为我们感兴趣的值设置一点，还要为每一个大于该值的值设置。这很可能会在大量写入的用例中引入性能问题。

理想情况下，我们想要的是具有范围编码位图的功能和相等编码的效率。接下来，我们将讨论位切片索引，看看它如何帮助我们实现我们想要的。

## 位切片索引

如果我们想使用范围编码位图来表示从 0 到 956 的每一个可能值，我们必须使用 957 位图。虽然这可以工作，但这并不是最有效的方法，而且当可能值的基数非常高时，我们需要维护的位图数量可能会变得过高。位切片索引使我们能够以更有效的方式表示这些相同的值。

让我们看看我们的示例数据，并讨论如何使用位切片索引来表示它。

![](https://uploads-ssl.webflow.com/62fe6fb36d2e0b5c203ee7c3/6324dcdcbc7729005934d698_captive-bsi-base10.png)

_十进制，位切片索引_

请注意，我们已经将我们的值划分为三个以 10 为基数的组成部分。第一列比特表示 003 值，这是圈养海牛的数量。003 的组件 0 是 3，所以我们在组件 0 的第 3 行设置了一个位。003 的组件 1 和 2 都是 0，所以我们在组件 1 的行 0 和组件 2 的行 0 中设置位。我们的十进制索引中的每个组件都需要 10 个位图来表示所有可能的值，因此在我们需要表示 0 到 956 之间的值的圈养示例中，我们只需要（3 x 10）=30 个位图（而如果我们为每个不同的值使用一个位图，则需要 957 个位图）。

所以这很好，但我们基本上刚刚找到了一种更有效的相等编码策略。让我们看看当我们将位切片索引与范围编码相结合时会是什么样子。

## 范围编码位切片索引

![](https://uploads-ssl.webflow.com/62fe6fb36d2e0b5c203ee7c3/6324dd193bb4e80fd93e0b4f_captive-bsi-range-encoded-base10.png)

_范围编码，十进制，位切片索引_

请注意，每个组件中最重要的值（在基数为10的情况下为9）始终为 1。正因为如此，我们不需要存储最高值。因此，对于十进制的范围编码的位切片索引，我们只需要9个位图来表示一个组件。除此之外，我们还需要存储一个名为“Not Null”的位图，它指示是否为该列设置了值。下一个图表显示了生成的位图。

![](https://uploads-ssl.webflow.com/62fe6fb36d2e0b5c203ee7c3/6324dd62797efe87f0dfff68_captive-bsi-range-encoded-base10-not-null.png)

_范围编码，十进制，位切片索引，不为空_

因此，对于三位数的值，我们需要（（3 x 9）+1）=28 个位图来表示 0 到 999 范围内的任何值。现在我们有了一种非常有效的存储值的方法，并且我们获得了范围编码的好处，因此我们可以执行对范围进行过滤的查询。让我们更进一步，尝试对我们的值范围的二进制表示进行编码。

### 二进制的组件

如果我们使用二进制的组件而不是将 Captivity 值表示为十进制的组件，那么我们最终得到的是一组范围编码的位切片索引，如下所示：

![](https://uploads-ssl.webflow.com/62fe6fb36d2e0b5c203ee7c3/6324dd9c01e7bce0b01db246_captive-bsi-range-encoded-base2.png)

_范围编码，二进制，位切片索引_

第一列比特表示以 2 为基数的值 000000011，这是圈养海牛的数量（以 10 为基数为 3）。由于 000000011 的组件 0 和组件 1 都是 1，我们在组件 0 的行 1 和组件 1 的行 1 中设置一个位。由于 000000011的 其余组件都是 0，我们在组件 2 到 9 的第 0 行设置了一个比特，也因为这些组件是范围编码的，我们在每个大于 0 的值中设置一个比特。在二进制的组件的情况下，这意味着我们还为组件 2 到 9设置了行 1 中的位。

但请记住，就像我们之前在十进制表示的位图 9 中看到的那样，位图 1 总是一个，所以我们不需要存储它。这就给我们留下了这样的方式：

![](https://uploads-ssl.webflow.com/62fe6fb36d2e0b5c203ee7c3/6324dddadece9c315c62a231_captive-bsi-range-encoded-base2-not-null.png)

_范围编码，二进制，不为空的位切片索引_

通过这种编码，我们可以仅用 10 个位图来表示样本值的范围！此外，请注意，二进制、范围编码、位切片索引是整数值的二进制表示的反。这告诉我们，我们可以仅使用（n+1）位图（其中附加位图是“Not Null”位图）来表示基数为n的任何范围的值。这意味着我们可以对大整数值执行范围查询，而不需要存储不合理数量的位图。

## FeatureBase 中的范围编码位图

通过在 FeatureBase 中实现范围编码位图，用户现在可以存储涉及数十亿个对象的整数值，并可以非常快速地执行按范围进行过滤的查询。我们还支持像 Sum（）这样的聚合查询。圈养的有翼脊椎动物的总数是多少？没问题。

作为最后一个练习，让我们演示如何在 FeatureBase 中存储和查询示例圈养数据。

\# 创建一个名为“animals”的索引。
curl -X POST localhost:10101/index/animals

\# 创建一个“特征（traits）”视图来存放圈养（captivity）值。
curl localhost:10101/index/animals/frame/traits \\  
 -X POST \\  
 -d '{"options":{"rangeEnabled": true,  
                    "fields": \[{"name": "captivity",  
                                "type": "int",  
                                "min": 0,  
                                "max": 956}\]  
                   }  
        }'

\# 将圈养值添加到字段中。
curl localhost:10101/index/animals/query \\  
 -X POST \\  
 -d 'SetFieldValue(frame=traits, col=1,  captivity=3)  
     SetFieldValue(frame=traits, col=2,  captivity=392)  
     SetFieldValue(frame=traits, col=3,  captivity=47)  
     SetFieldValue(frame=traits, col=4,  captivity=956)  
     SetFieldValue(frame=traits, col=5,  captivity=219)  
     SetFieldValue(frame=traits, col=6,  captivity=14)  
     SetFieldValue(frame=traits, col=7,  captivity=47)  
     SetFieldValue(frame=traits, col=8,  captivity=504)  
     SetFieldValue(frame=traits, col=9,  captivity=21)  
     SetFieldValue(frame=traits, col=10, captivity=0)  
     SetFieldValue(frame=traits, col=11, captivity=123)  
     SetFieldValue(frame=traits, col=12, captivity=318)  
 '

\# 查询所有圈养值超过 100 个的动物。
curl localhost:10101/index/animals/query \\  
 -X POST \\  
 -d 'Range(frame=traits, captivity > 100)'

\# 查询圈养动物总数。
curl localhost:10101/index/animals/query \\  
 -X POST \\  
 -d 'Sum(frame=traits, field=captivity)'

## 结论

我在这篇文章中描述的例子展示了我们如何使用位切片索引来显著减少表示范围整数值所需的 bitmap 数量。
通过对索引应用范围编码，我们能够对数据执行各种范围查询。下面的图表比较了我们讨论的不同方法。

![](https://uploads-ssl.webflow.com/62fe6fb36d2e0b5c203ee7c3/6324de501a3ea21632e162bd_example-comparison.png)

_对比图_

试试看，让我们知道你的想法。我们一直在寻求改进，并感谢您的任何反馈！

