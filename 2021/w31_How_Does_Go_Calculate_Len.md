# Go 语言是如何计算 len() 的
- 原文地址：https://tpaschalis.github.io/golang-len/
- 原文作者：Paschalis Tsilias
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w31_How_Does_Go_Calculate_Len.md
- 译者：[twx](https://github.com/1-st)
- 校对：[Cluas](https:/github.com/Cluas) , [cvley](https://github.com/cvley)

撰写此文的动力源于不久前在 Gophers Slack 上的一个问题 ：一位开发人员想知道在哪里可以找到更多关于 len 函数的信息。

> I want to know how the len func gets called. (我想知道 len 函数是怎么被调用的。)

很快，有人回答了正确答案

> It doesn’t. Len is compiler magic, not an actual function call. (Len 是编译器魔术，而不是一个实际的函数调用。)

> …… all the types len works on have the same header format, the compiler just treats the object like a header and returns the integer representing the length of elements (所有 len 处理的类型都有相同的头部格式，编译器只是将对象当作头部对待，并返回表示元素长度的整数)

虽然这些答案在技术上是正确的，但我认为用简洁的语言展开构成这个"魔法"的层次结构会很棒！这也是一个很好的小练习，可以让你更深入地了解 Go 编译器的内部工作原理。

仅供参考，本帖中的所有链接都指向即将发布的 Go 1.17 分支 (https://github.com/golang/go/tree/release-branch.go1.17).

## 小插曲
一些背景信息可能有助于理解这篇文章。

Go 编译器由四个主要阶段组成。你可以从 这里 (https://golang.org/src/cmd/compile/README) 开始阅读。前两个一般称为编译器"前端"，而后两个也称为编译器"后端"。

* **解析**; 对源文件进行词法分析和语法分析，并为每个源文件构建一个语法树
* **AST 抽象语法树转换和类型检查**; 将语法树转换为编译器的 AST 表示形式，并对 AST 树进行类型检查
* **生成 SSA 静态单赋值**; AST 树被转换为 Static Single Assignment (SSA 静态单赋值) 形式，这是一种可以实现优化的较低级别的中间表示形式
* **生成机器码**; SSA 经过另一个特定于机器的优化过程，然后传递给汇编程序，转换为机器代码并写入最终的二进制文件


让我们开始深入吧！

## 入口
Go 编译器的入口点 (毫不奇怪) 是 *compile/internal/gc* 包中的 main() 函数 (https://github.com/golang/go/blob/release-branch.go1.17/src/cmd/compile/internal/gc/main.go)

如注释所示，这个函数负责解析 Go 源文件，对解析后的 Go 包进行类型检查，将所有内容编译为机器代码并为编译过的包编写定义。

最初发生的事情之一就是类型检查。[typecheck.InitUniverse()](https://github.com/golang/go/blob/release-branch.go1.17/src/go/types/universe.go) ，它定义了基本类型、内置函数和操作数。

在这里，我们可以看到所有内置函数是如何被匹配到一个“操作”的，我们可以使用 ir.OLEN 来跟踪 len() 调用的步骤。

```go
var builtinFuncs = [...]struct {
	name string
	op   ir.Op
}{
	{"append", ir.OAPPEND},
	{"cap", ir.OCAP},
	{"close", ir.OCLOSE},
	{"complex", ir.OCOMPLEX},
	{"copy", ir.OCOPY},
	{"delete", ir.ODELETE},
	{"imag", ir.OIMAG},
	{"len", ir.OLEN},
	{"make", ir.OMAKE},
	{"new", ir.ONEW},
	{"panic", ir.OPANIC},
	{"print", ir.OPRINT},
	{"println", ir.OPRINTN},
	{"real", ir.OREAL},
	{"recover", ir.ORECOVER},
}
```
稍后在 *InitUniverse* 中，可以看到 *okfor* 数组的初始化，它定义了各种操作数的有效类型; 例如，哪些类型应该允许 *+* 操作符使用。
```go
	if types.IsInt[et] || et == types.TIDEAL {
		...
		okforadd[et] = true
		...
	}
	if types.IsFloat[et] {
		...
		okforadd[et] = true
		...
		}
	if types.IsComplex[et] {
		...
		okforadd[et] = true
		...
	}
```
同样，我们可以看到所有的类型将成为 len() 的有效输入
```go
	okforlen[types.TARRAY] = true
	okforlen[types.TCHAN] = true
	okforlen[types.TMAP] = true
	okforlen[types.TSLICE] = true
	okforlen[types.TSTRING] = true
```
## 编译器前端
接下来是编译的下一个主要步骤，这时候我们对输入进行解析并从 noder.LoadPackage(flag.Args()) 开始进行类型检查。(https://github.com/golang/go/blob/release-branch.go1.17/src/cmd/compile/internal/gc/main.go#L191-L192)

再深入一些，我们可以看到每个文件被单独解析，然后在五个不同的阶段进行类型检查。(https://github.com/golang/go/blob/release-branch.go1.17/src/cmd/compile/internal/noder/noder.go#L40-L64)

```plain
Phase 1: const, type, and names and types of funcs. (常量，类型，标识符以及函数的类型)
Phase 2: Variable assignments, interface assignments, alias declarations.（有效的赋值，接口赋值，别名声明）
Phase 3: Type check function bodies.（函数体类型检查）
Phase 4: Check external declarations.（检查外部声明）
Phase 5: Verify map keys, unused dot imports.（检验 Map 的键和未使用的点引入）
```
一旦在最后的类型检查阶段遇到 len 语句，它就会被转换为 *UnaryExpr*，因为它实际上不会最终成为一个函数调用。

编译器隐式获取参数的地址，并使用 *okforlen* 数组来验证参数的合法性或发出相关的错误消息。
```go
// typecheck1 should ONLY be called from typecheck.
func typecheck1(n ir.Node, top int) ir.Node {
	if n, ok := n.(*ir.Name); ok {
		typecheckdef(n)
	}

	switch n.Op() {
	...
	case ir.OCAP, ir.OLEN:
		n := n.(*ir.UnaryExpr)
		return tcLenCap(n)
	}
}

// tcLenCap typechecks an OLEN or OCAP node.
func tcLenCap(n *ir.UnaryExpr) ir.Node {
	n.X = Expr(n.X)
	n.X = DefaultLit(n.X, nil)
	n.X = implicitstar(n.X)
	...
	var ok bool
	if n.Op() == ir.OLEN {
		ok = okforlen[t.Kind()]
	} else {
		ok = okforcap[t.Kind()]
	}
	if !ok {
		base.Errorf("invalid argument %L for %v", l, n.Op())
		n.SetType(nil)
		return n
	}

	n.SetType(types.Types[types.TINT])
	return n
}
```
返回到主编译器流程，在所有内容都进行了类型检查之后，所有的函数都将被排队。(https://github.com/golang/go/blob/release-branch.go1.17/src/cmd/compile/internal/gc/main.go#L277-L287)

在 *compileFunctions()* 中，队列中的每个元素都通过 *ssagen.Compile* 传递
```go
	compile = func(fns []*ir.Func) {
		wg.Add(len(fns))
		for _, fn := range fns {
			fn := fn
			queue(func(worker int) {
				ssagen.Compile(fn, worker)
				compile(fn.Closures)
				wg.Done()
			})
		}
	}
	...
	compile(compilequeue)
```
在 *buildssa* 和 *genssa* 之后，再深入几层，我们终于可以将 AST 树中的 len 表达式转换为 SSA。

现在很容易看到每个可用类型是如何处理的！
```go
// expr converts the expression n to ssa, adds it to s and returns the ssa result.
func (s *state) expr(n ir.Node) *ssa.Value {
	...
	switch n.Op() {
	case ir.OLEN, ir.OCAP:
		n := n.(*ir.UnaryExpr)
		switch {
		case n.X.Type().IsSlice():
			op := ssa.OpSliceLen
			if n.Op() == ir.OCAP {
				op = ssa.OpSliceCap
			}
			return s.newValue1(op, types.Types[types.TINT], s.expr(n.X))
		case n.X.Type().IsString(): // string; not reachable for OCAP
			return s.newValue1(ssa.OpStringLen, types.Types[types.TINT], s.expr(n.X))
		case n.X.Type().IsMap(), n.X.Type().IsChan():
			return s.referenceTypeBuiltin(n, s.expr(n.X))
		default: // array
			return s.constInt(types.Types[types.TINT], n.X.Type().NumElem())
		}
		...
	}
	...
}
```
## Arrays
对于数组，我们只需基于输入数组的 *NumElem ()* 方法返回一个常量整数，该方法只访问输入数组的 *Bound* 字段。
```go
// Array contains Type fields specific to array types.
type Array struct {
	Elem  *Type // element type
	Bound int64 // number of elements; <0 if unknown yet
}

func (t *Type) NumElem() int64 {
	t.wantEtype(TARRAY)
	return t.Extra.(*Array).Bound
}
```
## Slices, Strings
对于切片和字符串，我们必须了解 *ssa.OpSliceLen* 和 *ssa.OpStringLen* 是如何处理的。

当这两个调用中的任何一个在展开阶段遇到 *rewriteSelect* 方法时，编译器使用类似 *offset+x.ptrSize* 的指针算法递归地遍历切片和字符串以找出它们的大小
```go
func (x *expandState) rewriteSelect(leaf *Value, selector *Value, offset int64, regOffset Abi1RO) []*LocalSlot {
	switch selector.Op {
	...
	case OpStringLen, OpSliceLen:
		ls := x.rewriteSelect(leaf, selector.Args[0], offset+x.ptrSize, regOffset+RO_slice_len)
		locs = x.splitSlots(ls, ".len", x.ptrSize, leafType)
	...
	}
	return locs
```
## Maps, Channels
最后，对于 Map 和 Channel，我们使用 *referenceTypeBuiltin* 辅助函数。它的内部工作方式有点神奇，但是它最终做的是获取 map/chan 参数的地址并使用零偏移量引用它的结构布局，很像 *unsafe.Pointer(uintptr(unsafe.Pointer(s)))* 那样最终返回第一个结构字段的值。
```go
// referenceTypeBuiltin generates code for the len/cap builtins for maps and channels.
func (s *state) referenceTypeBuiltin(n *ir.UnaryExpr, x *ssa.Value) *ssa.Value {
	if !n.X.Type().IsMap() && !n.X.Type().IsChan() {
		s.Fatalf("node must be a map or a channel")
	}
	// if n == nil {
	//   return 0
	// } else {
	//   // len
	//   return *((*int)n)
	//   // cap
	//   return *(((*int)n)+1)
	// }
	lenType := n.Type()
	nilValue := s.constNil(types.Types[types.TUINTPTR])
	cmp := s.newValue2(ssa.OpEqPtr, types.Types[types.TBOOL], x, nilValue)
	b := s.endBlock()
	b.Kind = ssa.BlockIf
	b.SetControl(cmp)
	b.Likely = ssa.BranchUnlikely

	bThen := s.f.NewBlock(ssa.BlockPlain)
	bElse := s.f.NewBlock(ssa.BlockPlain)
	bAfter := s.f.NewBlock(ssa.BlockPlain)

	...
	switch n.Op() {
	case ir.OLEN:
		// length is stored in the first word for map/chan
		s.vars[n] = s.load(lenType, x)
	...
	return s.variable(n, lenType)
}
```
*hmap* 和 *hchan* 结构的定义表明，它们的第一个字段确实包含 *Len()* 所需要的东西，分别是 *count int // # live cells == size of map* (Map 的大小) 和 *qcount uint // total data in the queue* (队列里所有的数据)。

```go
type hmap struct {
	count     int // # live cells == size of map.  Must be first (used by len() builtin)
	flags     uint8
	B         uint8
	noverflow uint16
	hash0     uint32

	buckets    unsafe.Pointer
	oldbuckets unsafe.Pointer
	nevacuate  uintptr

	extra *mapextra
}

type hchan struct {
	qcount   uint           // total data in the queue
	dataqsiz uint
	buf      unsafe.Pointer
	elemsize uint16
	closed   uint32
	elemtype *_type
	sendx    uint
	recvx    uint
	recvq    waitq
	sendq    waitq

	lock mutex
}
```
## 临别赠言
就是这样！这篇文章并没有我想象的那么长，我希望你也能对它感兴趣。

我对于 Go 编译器的内部工作几乎没有经验，所以有些地方可能会有错。除此之外，随着泛型和新类型系统在接下来的几个 Go 版本中的出现，很多事情也都会发生改变。但我希望我至少提供了一种方法，可以让你接下来自己深入探索。

请不要犹豫，向我提出意见、建议、新文章的想法，或者仅仅是谈一谈 Go

下次见！

*于 2021 年 7 月 31 日撰写*
