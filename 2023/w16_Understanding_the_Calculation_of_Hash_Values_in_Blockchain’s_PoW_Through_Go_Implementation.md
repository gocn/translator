- 原文地址：https://medium.com/@shuntaro-okuma/understanding-the-calculation-of-hash-values-in-blockchains-pow-through-go-implementation-7c4b45ed654d
- 原文作者：Shuntaro
- 本文永久链接：https://github.com/gocn/translator/blob/master/2023/w16_Understanding_the_Calculation_of_Hash_Values_in_Blockchain’s_PoW_Through_Go_Implementation.md
- 译者：[haoheipi](https://github.com/haoheipi)
- 校对：[]()

In this article, I explain the calculation method of the Proof of Work (PoW) algorithm in blockchain with concrete examples. I will also show an implementation example in the Go language.

What is a Nonce? What is Difficulty? How are hash values calculated? This article will help you understand these concepts.

## Structure of Blockchain and Calculation of PoW

Blockchain is composed of a list structure where multiple blocks are connected.

Each block in the diagram below is represented by a green box, and they are connected by hash values, which is why it is called a blockchain.

![](../static/images/2023/w16/1.png)

Each block contains the hash value of the previous block, a Nonce value, a timestamp, and transactions.

These hash values and Nonce values are closely related in the PoW algorithm.

- Hash value A unique value calculated based on the data of a block (previous block’s hash, Nonce value, timestamp, transactions). Typically, it is calculated using a cryptographic hash function such as SHA-256. Hash values cannot be restored to the original data because the information is dropped during calculation. If the original data changes even slightly, the hash value will become a completely different value. Due to these characteristics, hash values are used for tampering detection of data.

- Nonce value Nonce stands for “number used once” and is a unique numeric value added to the block data to adjust the hash value to meet the Difficulty requirements. Nonce usually starts at 0 and increments. The Difficulty requirement means that the hash value is below a certain target value. Difficulty is a threshold introduced to maintain a constant block generation speed.

The calculation of PoW is as follows:

1. Calculate the hash of the block while incrementing the Nonce from 0
2. Check if the hash value meets the Difficulty conditions
3. Continue changing the Nonce value until a hash that meets the conditions is found
4. Add the block to the blockchain when a hash that meets the conditions is found


# Simple example

Let’s show an example with Go language implementation.

The calculation conditions are:

- The data of the block is the string “Hello, world!”
- Difficulty is set to 4 (meaning the calculated hash value must start with “0000”)

The calculation steps are as follows:

1. Start with Nonce at 0.
2. Combine the block data and Nonce, i.e., the calculation target is the string “Hello, world!0.”
3. Apply the SHA-256 hash function to “Hello, world!0” and calculate the hash value.
4. Check if the calculated hash value meets the Difficulty conditions (starting with “0000”).
5. If not met, increase the Nonce by 1 and repeat steps 2–4.
6. If met, the calculation is complete.

The implementation in Go language looks like this:

```golang
package main

import (
 "crypto/sha256"
 "encoding/hex"
 "fmt"
 "strings"
)

func main() {
 data := "Hello, world!"
 difficulty := 4
 target := strings.Repeat("0", difficulty) // "0000"

 // 1. Start with nonce at 0
 nonce := 0

 for {
  // 2. Combine the block data and Nonce, i.e., the calculation target is the string "Hello, world!0."
  dataToHash := data + fmt.Sprint(nonce)

  // 3. Apply the SHA-256 hash function to "Hello, world!0" and calculate the hash value.
  hasher := sha256.New()
  hasher.Write([]byte(dataToHash))
  hash := hex.EncodeToString(hasher.Sum(nil))

  // 4. Check if the calculated hash value meets the Difficulty conditions (starting with "0000").
  if strings.HasPrefix(hash, target) {
   // 6. If true, the calculation is complete.
   fmt.Printf("Found a valid hash: %s (Nonce: %d)\n", hash, nonce)
   break
  } else {
   // 5. If not met, increase the Nonce by 1 and repeat steps 2–4.
   nonce++
  }
 }
}
```

When you run it, you get a result like this:

```golang
Found a valid hash: 0000c3af42fc31103f1fdc0151fa747ff87349a4714df7cc52ea464e12dcd4e9 (Nonce: 4250)
```

In this calculation example, a hash value that meets the Difficulty condition (hash starts with “0000”) was found when Nonce is 4250.


## Real-life Example

In an actual blockchain, the calculation of hash values and Nonce is based on the block header, which includes information such as transaction data within the block, the hash value of the previous block, and a timestamp.

Assume we have block data like this:

- Hash of the previous block: abcd1234
- Timestamp: 1633022800
- Transaction data: {Sender: “Alice”, Recipient: “Bob”, Amount: 10}
- Initial Nonce value: 0
- Difficulty: 3

The implementation looks like this:

```golang
package main

import (
 "crypto/sha256"
 "encoding/hex"
 "fmt"
 "strings"
)

type Block struct {
 Timestamp     int64
 Transactions  string
 PrevBlockHash string
 Nonce         int
}

func main() {
  block := &Block{
  Timestamp:     1633022800,
  Transactions:  `{Sender: "Alice", Recipient: "Bob", Amount: 10}`,
  PrevBlockHash: "abcd1234",
  Nonce:         0,
 }

  data := strconv.FormatInt(block.Timestamp, 10) + block.Transactions + block.PrevBlockHash + strconv.Itoa(block.Nonce)

 difficulty := 3
 target := strings.Repeat("0", difficulty) // "000"

 nonce := 0

 for {
  dataToHash := data + fmt.Sprint(nonce)

  hasher := sha256.New()
  hasher.Write([]byte(dataToHash))
  hash := hex.EncodeToString(hasher.Sum(nil))

  if strings.HasPrefix(hash, target) {
   fmt.Printf("Found a valid hash: %s (Nonce: %d)\n", hash, nonce)
   break
  } else {
   nonce++
  }
 }
}
```

When you run it, you get a result like this:

```golang
Found a valid hash: 000d162f9ed911a43771dcc0159a92a8372bf4aa9f452f6cbc195e000192c8c4 (Nonce: 8098)
```

By increasing the Nonce, we were able to generate different hash values and find a hash value that meets the Difficulty condition.


## Conclusion

This calculation is an essential process carried out before adding a block to the blockchain as part of PoW.

In reality, the Difficulty is much larger, and it takes longer to find a valid hash. This is what makes the blockchain difficult to tamper with and maintains the immutability of the data.

For example, if we set the Difficulty to 4 and run it, we get a result like this:

```golang
Found a valid hash: 0000cd54202992361b10644a6596b12e9d19e89fb8a325062fb0499dbe1a3a23 (Nonce: 13655)
```

The Nonce value has increased, which means it took more time to calculate.

As the Difficulty increases, the time it takes to calculate increases, and more computational resources are needed. As a result, miners worldwide are investing vast amounts of computational resources to find a hash value that meets the Difficulty condition before their competitors.

The Difficulty is adjusted across the entire blockchain network, and it is set so that blocks are generated at a specific time interval (e.g., about every 10 minutes for Bitcoin). This prevents transactions from never being stored in the blockchain due to no new blocks being generated.