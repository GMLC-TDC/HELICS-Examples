package main

import "os"
import "fmt"

func main() {
	fmt.Println("Token length is", len(os.Getenv("HELICSBOT_GH_TOKEN")), "(expected 40)")
}
