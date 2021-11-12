- 原文地址：https://venilnoronha.io/a-step-by-step-guide-to-mtls-in-go
- 原文作者：`Venil Noronha`
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w44_A_step_by_step_guide_to_mTLS_in_Go.md
- 译者：[朱亚光](https://github.com/zhuyaguang)
- 校对：

Ever wondered what mTLS (mutual TLS) looks like? Come, learn to implement mTLS using Golang and OpenSSL.

## Introduction

TLS (Transport Layer Security) provides the necessary encryption for applications when communicating over a network. HTTPS (Hypertext Transfer Protocol Secure) is an extension of HTTP that leverages TLS for security. The TLS technique requires a CA (Certificate Authority) to issue a X.509 digital certificate to a service, which is then handed over to the consumer of the service for it to validate it with the CA itself. mTLS extends the same idea to applications, for example, microservices wherein both the provider and the consumer require to produce their own certificates to the other party. These certificates are validated by both parties with their respective CAs. Once validated, the communication between the server/client or provider/consumer happens securely.

## The Implementation

### Step 1 - Build a simple HTTP Server and Client

Let’s first create a simple HTTP Server in `server.go` which responds with `Hello, world!` when requested for the `/hello` resource over port `8080`.

```
package main

import (
"io"
"log"
"net/http"
)

func helloHandler(w http.ResponseWriter, r *http.Request) {
// Write "Hello, world!" to the response body
io.WriteString(w, "Hello, world!\n")
}

func main() {
// Set up a /hello resource handler
http.HandleFunc("/hello", helloHandler)

// Listen to port 8080 and wait
log.Fatal(http.ListenAndServe(":8080", nil))
}
```

The Client simply requests for the `/hello` resource over port `8080` and prints the response body to `stdout`. Here is what `client.go` looks like:

```
package main

import (
"fmt"
"io/ioutil"
"log"
"net/http"
)

func main() {
// Request /hello over port 8080 via the GET method
r, err := http.Get("http://localhost:8080/hello")
if err != nil {
log.Fatal(err)
}

// Read the response body
defer r.Body.Close()
body, err := ioutil.ReadAll(r.Body)
if err != nil {
log.Fatal(err)
}

// Print the response body to stdout
fmt.Printf("%s\n", body)
}
```

Open an instance of the terminal and run the Server like so:

Open another instance of the terminal and run the Client:

You should see the following output from the Client.

### Step 2 - Generate and use the Certificates with the Server

Use the following command to generate the certificates. The command creates a 2048 bit key certificate which is valid for 10 years. Additionally, the `CN=localhost` asserts that the certificate is valid for the `localhost` domain.

```
openssl req -newkey rsa:2048 \
  -new -nodes -x509 \
  -days 3650 \
  -out cert.pem \
  -keyout key.pem \
  -subj "/C=US/ST=California/L=Mountain View/O=Your Organization/OU=Your Unit/CN=localhost"
```

You should now have `cert.pem` and `key.pem` in your directory.

Let’s now enable TLS over HTTP i.e. HTTPS on the Server. Replace the `http.ListenAndServe(":8080", nil)` call in `server.go` with `http.ListenAndServeTLS(":8443", "cert.pem", "key.pem", nil)` for the Server to listen to HTTPS connections over port `8443` while supplying the certificates generated earlier.

```
-// Listen to port 8080 and wait
-log.Fatal(http.ListenAndServe(":8080", nil))
+// Listen to HTTPS connections on port 8443 and wait
+log.Fatal(http.ListenAndServeTLS(":8443", "cert.pem", "key.pem", nil))
```

You can verify the Server’s working by running it and browsing to `https://localhost:8443/hello`.

![Secure Server](https://venilnoronha.io/assets/images/2018-09-04-a-step-by-step-guide-to-mtls-in-go/server_https.png)

Let’s now update `client.go` to connect to the Server over HTTPS.

```
-// Request /hello over port 8080 via the GET method
-r, err := http.Get("http://localhost:8080/hello")
+// Request /hello over HTTPS port 8443 via the GET method
+r, err := http.Get("https://localhost:8443/hello")
```

Since our Client doesn’t yet know about the certificates, running it should spit out the following error on the Server.

```
http: TLS handshake error from [::1]:59436: remote error: tls: bad certificate
```

On the Client, you should observe the following.

```
x509: certificate is not valid for any names, but wanted to match localhost
```

### Step 3 - Supply the Certificates to the Client

Update the `client.go` code to read the previously generated certificates, like so:

```
-// Request /hello over HTTPS port 8443 via the GET method
-r, err := http.Get("https://localhost:8443/hello")

+// Create a CA certificate pool and add cert.pem to it
+caCert, err := ioutil.ReadFile("cert.pem")
+if err != nil {
+log.Fatal(err)
+}
+caCertPool := x509.NewCertPool()
+caCertPool.AppendCertsFromPEM(caCert)
+
+// Create a HTTPS client and supply the created CA pool
+client := &http.Client{
+Transport: &http.Transport{
+TLSClientConfig: &tls.Config{
+RootCAs: caCertPool,
+},
+},
+}
+
+// Request /hello via the created HTTPS client over port 8443 via GET
+r, err := client.Get("https://localhost:8443/hello")
```

Here, we read the `cert.pem` file and supply it as the root CA when creating the Client. Running the Client should now successfully display the following.

### Final Step - Enable mTLS

On the Client, read and supply the key pair as the client certificate.

```
+// Read the key pair to create certificate
+cert, err := tls.LoadX509KeyPair("cert.pem", "key.pem")
+if err != nil {
+log.Fatal(err)
+}

...

-// Create a HTTPS client and supply the created CA pool
+// Create a HTTPS client and supply the created CA pool and certificate
client := &http.Client{
Transport: &http.Transport{
TLSClientConfig: &tls.Config{
RootCAs: caCertPool,
+Certificates: []tls.Certificate{cert},
},
},
}
```

On the Server, we create a similar CA pool and supply it to the TLS config to serve as the authority to validate Client certificates. We also use the same key pair for the Server certificate.

```
-// Listen to HTTPS connections on port 8443 and wait
-log.Fatal(http.ListenAndServeTLS(":8443", "cert.pem", "key.pem", nil))

+// Create a CA certificate pool and add cert.pem to it
+caCert, err := ioutil.ReadFile("cert.pem")
+if err != nil {
+log.Fatal(err)
+}
+caCertPool := x509.NewCertPool()
+caCertPool.AppendCertsFromPEM(caCert)
+
+// Create the TLS Config with the CA pool and enable Client certificate validation
+tlsConfig := &tls.Config{
+ClientCAs: caCertPool,
+ClientAuth: tls.RequireAndVerifyClientCert,
+}
+tlsConfig.BuildNameToCertificate()
+
+// Create a Server instance to listen on port 8443 with the TLS config
+server := &http.Server{
+Addr:      ":8443",
+TLSConfig: tlsConfig,
+}
+
+// Listen to HTTPS connections with the server certificate and wait
+log.Fatal(server.ListenAndServeTLS("cert.pem", "key.pem"))
```

Run `server.go` and then `client.go` and you should see a success message on the Client, like so:

### All Together

Finally, the `server.go` looks like the following.

```
package main

import (
"crypto/tls"
"crypto/x509"
"io"
"io/ioutil"
"log"
"net/http"
)

func helloHandler(w http.ResponseWriter, r *http.Request) {
// Write "Hello, world!" to the response body
io.WriteString(w, "Hello, world!\n")
}

func main() {
// Set up a /hello resource handler
http.HandleFunc("/hello", helloHandler)

// Create a CA certificate pool and add cert.pem to it
caCert, err := ioutil.ReadFile("cert.pem")
if err != nil {
log.Fatal(err)
}
caCertPool := x509.NewCertPool()
caCertPool.AppendCertsFromPEM(caCert)

// Create the TLS Config with the CA pool and enable Client certificate validation
tlsConfig := &tls.Config{
ClientCAs: caCertPool,
ClientAuth: tls.RequireAndVerifyClientCert,
}
tlsConfig.BuildNameToCertificate()

// Create a Server instance to listen on port 8443 with the TLS config
server := &http.Server{
Addr:      ":8443",
TLSConfig: tlsConfig,
}

// Listen to HTTPS connections with the server certificate and wait
log.Fatal(server.ListenAndServeTLS("cert.pem", "key.pem"))
}
```

The `client.go` file looks like so:

```
package main

import (
"crypto/tls"
"crypto/x509"
"fmt"
"io/ioutil"
"log"
"net/http"
)

func main() {
// Read the key pair to create certificate
cert, err := tls.LoadX509KeyPair("cert.pem", "key.pem")
if err != nil {
log.Fatal(err)
}

// Create a CA certificate pool and add cert.pem to it
caCert, err := ioutil.ReadFile("cert.pem")
if err != nil {
log.Fatal(err)
}
caCertPool := x509.NewCertPool()
caCertPool.AppendCertsFromPEM(caCert)

// Create a HTTPS client and supply the created CA pool and certificate
client := &http.Client{
Transport: &http.Transport{
TLSClientConfig: &tls.Config{
RootCAs: caCertPool,
Certificates: []tls.Certificate{cert},
},
},
}

// Request /hello via the created HTTPS client over port 8443 via GET
r, err := client.Get("https://localhost:8443/hello")
if err != nil {
log.Fatal(err)
}

// Read the response body
defer r.Body.Close()
body, err := ioutil.ReadAll(r.Body)
if err != nil {
log.Fatal(err)
}

// Print the response body to stdout
fmt.Printf("%s\n", body)
}
```

## Conclusion

Golang makes it really easy to implement mTLS, and this one’s just ~100 LOC.

___

I’d love to hear what you think.