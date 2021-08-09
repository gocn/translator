# How does go calculate len()?
- 原文地址：https://tpaschalis.github.io/golang-len/
- 原文作者：Paschalis Tsilias
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w31_How_Does_Go_Calculate_Len.md
- 译者：[twx](https://github.com/1-st)
- 校对：[]()

The impetus for this post was a question on the Gophers Slack a while back. A fellow developer wanted to know where to find more information on len.

> I want to know how the len func gets called.

People chimed in quickly with a correct answer

> It doesn’t. Len is compiler magic, not an actual function call.

> … all the types len works on have the same header format, the compiler just treats the object like a header and returns the integer representing the length of elements

And while those answers are technically true, I thought it would be nice to unfurl the layers that make up this ‘magic’ in a concise explanation! It was also a nice little exercise into getting more insight about the inner workings of the Go compiler.

FYI, all links in this post point to the soon-to-be-released [Go 1.17 branch](https://github.com/golang/go/tree/release-branch.go1.17).

## A small interlude
Some background information which may be helpful in understanding the rest of this post.

The Go compiler consists of four main phases. You can start reading about them here. The first two are generally referred to as the compiler ‘frontend’, while the latter two are also called the compiler ‘backend’.

* **Parsing**; the source files are tokenized, parsed, and a syntax tree is constructed for each source file.
* **AST transformations and type-checking**; the syntax tree is converted to the compiler’s AST representation and the AST tree is type-checked.
* **Generic SSA**; the AST tree is converted into Static Single Assignment (SSA) form, a lower-level intermediate representation where optimizations can be implemented.
* **Generating machine code**; the SSA goes through another machine-specific optimization process, and is afterwards passed to the assembler to be translated to machine code and written out to the final binary.


Let’s dive back in!

## The entrypoint
The entrypoint of the Go compiler is (unsurprisingly) the [main()](https://github.com/golang/go/blob/release-branch.go1.17/src/cmd/compile/internal/gc/main.go) function in the *compile/internal/gc package* .

As the docstring suggests, this function is responsible for parsing Go source files, type-checking the parsed Go package, compiling everything to machine code and writing the compiled package definition.

One of the things that takes place early on is [typecheck.InitUniverse()](https://github.com/golang/go/blob/release-branch.go1.17/src/go/types/universe.go) which defines the basic types, built-in functions and operands.

There, we see how all built-in functions are matched to an ‘operation’ and we can use *ir.OLEN* to trace the steps of a call to len.

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
Later on in *InitUniverse*, one can see the initialization of the *okfor* arrays, which define the valid types for various operands; for example which types should be allowed for the *+* operator.
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
In the same way, we can see all types which will be valid inputs for len()
```go
	okforlen[types.TARRAY] = true
	okforlen[types.TCHAN] = true
	okforlen[types.TMAP] = true
	okforlen[types.TSLICE] = true
	okforlen[types.TSTRING] = true
```
## The compiler ‘frontend’
Moving on to the next major steps in the compilation process, we reach the point where the input is parsed and typechecked starting with [noder.LoadPackage(flag.Args())](https://github.com/golang/go/blob/release-branch.go1.17/src/cmd/compile/internal/gc/main.go#L191-L192).

A few levels deeper we can see each file being [parsed](https://github.com/golang/go/blob/release-branch.go1.17/src/cmd/compile/internal/noder/noder.go#L40-L64) individually and then type-checked in five distinct phases.

```
Phase 1: const, type, and names and types of funcs.
Phase 2: Variable assignments, interface assignments, alias declarations.
Phase 3: Type check function bodies.
Phase 4: Check external declarations.
Phase 5: Verify map keys, unused dot imports.
```
Once the len statement is encountered in the last type-checking phase, it’s transformed to a *UnaryExpr*, as it won’t actually end up being a function call.

The compiler implicitly takes the argument’s address and uses the *okforlen* array to verify the argument’s legality or emit a relevant error message.
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
Back to the main compiler flow and after everything is type-checked, all functions are [enqueued to be compiled](https://github.com/golang/go/blob/release-branch.go1.17/src/cmd/compile/internal/gc/main.go#L277-L287).

In compileFunctions() each element in the queue is passed through *ssagen.Compile*
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
where a few layers deep, after *buildssa* and *genssa* and we finally get to convert the len expression in the AST tree to SSA.

At this point it’s easy to see how each one of the available types is handled!
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
For *arrays* we just return an constant integer based on the input array’s *NumElem()* method which just accesses the Bound field of the input array.
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
For slices and strings, we have to take a peek at how *ssa.OpSliceLen* and *ssa.OpStringLen* are handled.

When either of those calls are lowered in the Late Expansion stage and the *rewriteSelect* method, slices and strings are recursively walked to find out their size using pointer arithmetic like *offset+x.ptrSize*
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
Finally for maps and channels we use the *referenceTypeBuiltin* helper. Its inner workings are a little magical, but what it ultimately does is take the address of the map/chan argument and reference its struct layout with zero offset, much like *unsafe.Pointer(uintptr(unsafe.Pointer(s)))* which ends up returning the value of first struct field.
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
The definitions of the *hmap* and *hchan* structs show that their first fields **do** indeed contain what we need for *len* i.e. the live map cells and channel queue data respectively.

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
## Parting words
Aaaand that’s all! This post wasn’t as lengthy as I thought it would be; I just hope it was interesting to you as well.

I’ve got little experience with the inner workings of the Go compiler, so some things may be amiss. Also, many things are subject to change in the very near future, especially with generics and the new type system coming in the next couple of Go versions, but at least I hope I’ve provided a way that you can use to start digging around for yourself.

In any case, please don’t hesitate to reach out for comments, suggestions, ideas for new posts or simply talk about Go!

Until next time, bye!

*Written on July 31, 2021*