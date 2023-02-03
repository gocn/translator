# 在 Go 中实施简洁架构

- 原文地址：[Implementing Clean Architecture in GO | by Vidhyanshu Jain | Medium](https://vidhyanshu.medium.com/implementing-clean-architecture-in-go-56aca59311b3)
- 原文作者：[Vidhyanshu Jain](https://vidhyanshu.medium.com/?source=user_profile-------------------------------------)
- 本文永久链接：[translator/w04_Implementing_clean_architecture_in_Go.md at master · gocn/translator (github.com)](https://github.com/gocn/translator/blob/master/2023/w04_Implementing_clean_architecture_in_Go.md)
- 译者：[zxmfke](https://github.com/zxmfke)
- 校对：

已经有很多关于 [简洁架构](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)的文章了。它的主要价值在于能够维护无副作用的领域层，使我们能够不需要利用沉重的mock来测试核心业务逻辑。

通过写一个无需依赖的核心领域逻辑，以及外部适配器(成为它的数据库存储或者 API 层)来实现的。这些适配器依赖于领域，而不是领域依赖适配器。

在这篇文章，我们会看一下简洁架构是如何实现一个简单的 Go 项目。我们会提及一些额外的主题，例如容器化以及用 Swagger 实现 OpenAPI 规范。

虽然我将在文章中高亮了感兴趣的点，但你可以在 [我的Github](https://github.com/Wkalmar/toggl-deck-management-api) 上看看整个项目。

## 项目需求

我们要求提供一个 REST API 的实现来模拟一副牌。

我们将需要向你的 API 提供以下方法，以处理卡片和牌组：

- 创建一个新的**牌组**
- 打开一个**牌组**
- 抽一张**牌**

### 创建一个新的牌组

它将创建标准的 52 张法国扑克牌，它包括 4 个花色的所有 13 个等级：梅花（♣），方块（♦），红心（♥）和黑桃（♠）。在这个作业中，你不需要担心小丑牌的问题。

- 牌组是否要洗牌 - 默认情况下，这副牌是有顺序的。A-黑桃，2-黑桃，3-黑桃...然后是方块，梅花，然后是红心。
- 牌组是完整的，还是部分的 - 默认情况下它会返回标准的 52 张牌，不然就是按照请求想要的牌，就像这个例子 `?cards=AS,KD,AC,2C,KH`。

请求响应需要返回一个 JSON，包含：

- 牌组 id (**UUID**)
- 牌组是否随机 (**boolean**) 和牌组剩下多少张牌 (**integer**)

```json
{
    "deck_id": "a251071b-662f-44b6-ba11-e24863039c59",
    "shuffled": false,
    "remaining": 30
}
```



### 打开牌组

它将通过 UUID 返回一个给定的牌组。如果牌组无法被获取或者是无效的，它应该返回一个错误。这个方法将 "打开牌组"，意味着它将按照创建的顺序，列出所有的牌。

请求响应需要返回一个 JSON，包含：

- 牌组 id (UUID)
- 牌组是否随机 (**boolean**) 和牌组剩下多少张牌 (**integer**)
- 所有剩下的卡牌数组(卡牌对象)

```json
{
    "deck_id": "a251071b-662f-44b6-ba11-e24863039c59",
    "shuffled": false,
    "remaining": 3,
    "cards": [
        {
            "value": "ACE",
            "suit": "SPADES",
            "code": "AS"
        },
                {
            "value": "KING",
            "suit": "HEARTS",
            "code": "KH"
        },
        {
            "value": "8",
            "suit": "CLUBS",
            "code": "8C"
        }
    ]
}
```



### 抽牌

我们将从一个给定的牌组中抽出一张（几张）牌。如果这副牌无法被获取或无效，它应该返回一个错误。需要提供一个参数来定义从牌组中抽取多少张牌。

请求响应需要返回一个 JSON，包含：

- 所有抽取的卡牌数组(**卡牌对象**)

```json
{
    "cards": [
        {
            "value": "QUEEN",
            "suit": "HEARTS",
            "code": "QH"
        },
        {
            "value": "4",
            "suit": "DIAMONDS",
            "code": "4D"
        }
    ]
}
```



## 设计领域

由于领域是我们应用程序的一个组成部分，我们将从领域开始设计我们的系统。

让我们把 `Shape` 和 `Rank` 类型编码为 `iota`。如果你熟悉其他语言，你可能会认为它是一个 `enum`，这是非常整洁的，因为我们的任务假设了某种内置的顺序，所以针对这个问题我们可能会利用底层的数值。

```go
type Shape uint8

const (
    Spades Shape = iota
    Diamonds
    Clubs
    Hearts
)

type Rank int8

const (
    Ace Rank = iota
    Two
    Three
    Four
    Five
    Six
    Seven
    Eight
    Nine
    Ten
    Jack
    Queen
    King
)
```



完成上述编码后，我们可以将 `Card` 编码为 shape 和 rank 的组合。

```go
type Card struct {
    Rank  Rank
    Shape Shape
}
```



领域驱动设计的功能之一是[使非法状态无法表现](https://blog.janestreet.com/effective-ml-revisited/)，但由于所有 rank 和 shape 的组合都是有效的，所以创建一张卡片是非常直观的。

```go
func CreateCard(rank Rank, shape Shape) Card {
    return Card{
        Rank:  rank,
        Shape: shape,
    }
}
```



现在让我们看一下牌组。

```go
type Deck struct {
    DeckId   uuid.UUID
    Shuffled bool
    Cards    []Card
}
```



这副牌会有三种操作：创建牌组、抽牌和计算剩余牌。

```go
func CreateDeck(shuffled bool, cards ...Card) Deck {
    if len(cards) == 0 {
        cards = initCards()
    }
    if shuffled {
        shuffleCards(cards)
    }

    return Deck{
        DeckId:   uuid.New(),
        Shuffled: shuffled,
        Cards:    cards,
    }
}

func DrawCards(deck *Deck, count uint8) ([]Card, error) {
    if count > CountRemainingCards(*deck) {
        return nil, errors.New("DrawCards: Insuffucient amount of cards in deck")
    }
    result := deck.Cards[:count]
    deck.Cards = deck.Cards[count:]
    return result, nil
}

func CountRemainingCards(d Deck) uint8 {
    return uint8(len(d.Cards))
}
```



请注意，在抽牌时，我们会检查我们是否有足够的牌来进行操作。为了在逻辑里让程序知道无法继续操作，我们利用了 Go [多个返回值](https://go.dev/doc/effective_go#multiple-returns)的功能。

在这一点上，我们可以观察到简洁架构的一个重要好处：核心领域逻辑没有外部依赖，这大大简化了单元测试。虽然大多数都是微不足道的，为了简洁起见，我们将省略它们，接着让我们看看那些验证是否洗牌的测试

```go
func TestCreateDeck_ExactCardsArePassed_Shuffled(t *testing.T) {
    jackOfDiamonds := CreateCard(Jack, Diamonds)
    aceOfSpades := CreateCard(Ace, Spades)
    queenOfHearts := CreateCard(Queen, Hearts)
    cards := []Card{jackOfDiamonds, aceOfSpades, queenOfHearts}
    deck := CreateDeck(false, cards...)
    deckCardsCount := make(map[Card]int)
    for _, resCard := range deck.Cards {
        value, exists := deckCardsCount[resCard]
        if exists {
            value++
            deckCardsCount[resCard] = value
        } else {
            deckCardsCount[resCard] = 1
        }
    }
    for _, inputCard := range cards {
        value, found := deckCardsCount[inputCard]
        assert.True(t, found, "Expected all cards to be present")
        assert.Equal(t, 1, value, "Expected cards not to be duplicate")
    }
}
```



很明显，我们无法验证洗好的牌的顺序。我们可以做的是验证洗好的牌是否满足我们感兴趣的属性，即我们的每张牌都在，并且我们的牌中没有重复的牌。这样的技术非常类似于[基于属性的测试](https://dev.to/bohdanstupak1/property-based-tests-and-clean-architecture-are-perfect-fit-2f57)。

另外，值得一提的是，为了消除模板式的断言代码，我们利用了 [testify](https://github.com/stretchr/testify/assert) 库的优势。

## 提供 API

让我们先来定义下路由。

```go
func main() {
    r := gin.Default()
    r.POST("/create-deck", api.CreateDeckHandler)
    r.GET("/open-deck", api.OpenDeckHandler)
    r.PUT("/draw-cards", api.DrawCardsHandler)
    r.Run()
}
```



一些读者可能对根据上述要求，创建牌组这个路由将参数作为URL请求的一部分感到困惑，可能会考虑让这个路由用 GET 请求而不是 POST。 然而，GET 请求的一个重要前提是，它们表现出[一致性](https://www.restapitutorial.com/lessons/idempotency.html)，即每次请求的结果是一致的，而这个路由不是这样的。这就是我们坚持使用 POST 的原因。

路由对应的 Handler 遵循相同的模式。我们解析查询参数，根据这些参数创建一个领域实体，对其进行操作，更新存储并返回专属的 DTO。让我们来看看更多的细节。

```go
type CreateDeckArgs struct {
    Shuffled bool   `form:"shuffled"`
    Cards    string `form:"cards"`
}

type OpenDeckArgs struct {
    DeckId string `form:"deck_id"`
}

type DrawCardsArgs struct {
    DeckId string `form:"deck_id"`
    Count  uint8  `form:"count"`
}

func CreateDeckHandler(c *gin.Context) {
    var args CreateDeckArgs
    if c.ShouldBind(&args) == nil {
        var domainCards []domain.Card
        if args.Cards != "" {
            for _, card := range strings.Split(args.Cards, ",") {
                domainCard, err := parseCardStringCode(card)
                if err == nil {
                    domainCards = append(domainCards, domainCard)
                } else {
                    c.String(400, "Invalid request. Invalid card code "+card)
                    return
                }
            }
        }
        deck := domain.CreateDeck(args.Shuffled, domainCards...)
        storage.Add(deck)
        dto := createClosedDeckDTO(deck)
        c.JSON(200, dto)
        return
    } else {
        c.String(400, "Ivalid request. Expecting query of type ?shuffled=<bool>&cards=<card1>,<card2>,...<cardn>")
        return
    }
}

func OpenDeckHandler(c *gin.Context) {
    var args OpenDeckArgs
    if c.ShouldBind(&args) == nil {
        deckId, err := uuid.Parse(args.DeckId)
        if err != nil {
            c.String(400, "Bad Request. Expecing request in format ?deck_id=<uuid>")
            return
        }
        deck, found := storage.Get(deckId)
        if !found {
            c.String(400, "Bad Request. Deck with given id not found")
            return
        }
        dto := createOpenDeckDTO(deck)
        c.JSON(200, dto)
        return
    } else {
        c.String(400, "Bad Request. Expecing request in format ?deck_id=<uuid>")
        return
    }
}

func DrawCardsHandler(c *gin.Context) {
    var args DrawCardsArgs
    if c.ShouldBind(&args) == nil {
        deckId, err := uuid.Parse(args.DeckId)
        if err != nil {
            c.String(400, "Bad Request. Expecing request in format ?deck_id=<uuid>")
            return
        }
        deck, found := storage.Get(deckId)
        if !found {
            c.String(400, "Bad Request. Expecting request in format ?deck_id=<uuid>&count=<uint8>")
            return
        }
        cards, err := domain.DrawCards(&deck, args.Count)
        if err != nil {
            c.String(400, "Bad Request. Failed to draw cards from the deck")
            return
        }
        var dto []CardDTO
        for _, card := range cards {
            dto = append(dto, createCardDTO(card))
        }
        storage.Add(deck)
        c.JSON(200, dto)
        return
    } else {
        c.String(400, "Bad Request. Expecting request in format ?deck_id=<uuid>&count=<uint8>")
        return
    }
}
```



## 定义 OpenAPI 规范

我们对待 OpenAPI 规范的方式不仅是作为一个花哨的文档生成器（尽管对于我们的文章来说这已经足够了），也是作为一个描述 REST API 的标准，以简化客户的使用。

让我们先用声明性的注释来装饰我们的主方法。这些注释稍后将被用于自动生成 Swagger 规范。在[这里](https://github.com/swaggo/swag#declarative-comments-format)你可以查到格式。

```go
// @title Deck Management API
// @version 0.1
// @description This is a sample server server.
// @termsOfService http://swagger.io/terms/

// @contact.name API Support
// @contact.url http://www.swagger.io/support
// @contact.email support@swagger.io

// @license.name Apache 2.0
// @license.url http://www.apache.org/licenses/LICENSE-2.0.html

// @host localhost:8080
// @BasePath /
// @schemes http
func main() {
```



路由对应的 Handler 也是如此。让我们以其中一个为例看看。

```go
// CreateDeckHandler godoc
// @Summary Creates new deck.
// @Description Creates deck that can be either shuffled or unshuffled. It can accept the list of exact cards which can be shuffled or unshuffled as well. In case no cards provided it returns a deck with 52 cards.
// @Accept */*
// @Produce json
// @Param shuffled query bool  true  "indicates whether deck is shuffled"
// @Param cards    query array false "array of card codes i.e. 8C,AS,7D"
// @Success 200 {object} ClosedDeckDTO
// @Router /create-deck [post]
func CreateDeckHandler(c *gin.Context) {
```



现在让我们拉取 Swagger 库。

```shell
go get -v github.com/swaggo/swag/cmd/swag
go get -v github.com/swaggo/gin-sagger
go get -v github.com/swaggo/files
```



接着我们创建 swag。

```shell
swag init -g main.go --output docs
```



这个指令会在 docs 文件夹生成所需文件。

下一步在我们的 main.go 文件加入必要的 import。

```go
_ "toggl-deck-management-api/docs"
swaggerFiles "github.com/swaggo/files"
ginSwagger "github.com/swaggo/gin-swagger"
```



同样在路由的地方。

```go
url := ginSwagger.URL("/swagger/doc.json")
r.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler, url))
```



这些都完成之后，那我们现在可以运行我们的应用程序，看看通过 Swagger 生成的文档。


## API容器化

最后但并非最不重要的是我们将如何部署我们的应用程序。传统的方法是在一个专门的服务器上安装，并在安装的服务器上运行应用程序。

容器化是将 runtime 与应用程序一起打包的一种便捷方式，这可能在当我们想使用自动扩展功能，并且我们可能没有所有需要的服务器与环境安装在我们手中时，会很方便。

Docker 是最流行的容器化解决方案，所以我们将使用它。为此，我们将在我们项目的根目录下创建 dockerfile。

我们要做的第一件事是选择我们的应用程序将基于什么基础镜像。

```dockerfile
FROM golang:1.18-bullseye
```



之后，我们将把源代码复制到工作目录中并构建它

```dockerfile
RUN mkdir /app
COPY . /app
WORKDIR /app
RUN go build -o server .
```



最后一步是将端口暴露给外部宿主机并运行应用程序

```dockerfile
EXPOSE 8080
CMD [ "/app/server" ]
```



现在，我们的机器上已经安装了 Docker，我们可以通过以下方式运行应用程序

```shell
docker build -t <image-name> .
docker run -it --rm -p 8080:8080 <image-name>
```



## 总结

在这篇文章中，我们已经介绍了在 Go 中编写简洁架构 API 的整体过程。从经过测试的领域开始，为其提供一个API 层，使用 OpenAPI 标准对其进行记录，并将我们的 runtime 与应用程序打包在一起，从而简化了部署过程。