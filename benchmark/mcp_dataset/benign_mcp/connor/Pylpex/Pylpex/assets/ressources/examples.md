
## Recreation of Python's `len()` function
```pylpex
function len(array) {
  length = 0
  for value in array {
    length += 1
  }
  return length
}

len([1, 4, 5, 8, 51, 12]) // returns 6
```

## Factorial function
```pylpex
function factorial(n) {
    if n <= 1 {
        return 1
    } else {
        return n * factorial(n - 1)
    }
}

factorial(5) // returns 120
```