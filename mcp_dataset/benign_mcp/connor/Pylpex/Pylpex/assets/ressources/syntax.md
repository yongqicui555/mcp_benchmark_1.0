
# 📖 Syntaxe du langage **Pylpex**

> Ce document décrit la syntaxe complète du langage Pylpex, ses structures, opérateurs, types et particularités.
> La syntaxe est inspirée de Python, mais utilise **les accolades `{}`** pour délimiter les blocs de code au lieu de l’indentation.

---

## 🗒️ Commentaires

```pylpex
// Commentaire sur une seule ligne

/*
    Commentaire multi-lignes
*/
```

---

## 🔢 Types de données

| Type             | Exemple                | Description         |
| ---------------- | ---------------------- | ------------------- |
| **Entier**       | `42`                   | Nombre entier       |
| **Flottant**     | `3.14`                 | Nombre à virgule    |
| **Booléen**      | `true`, `false`        | Valeur logique      |
| **Chaîne**       | `"Hello"` ou `'World'` | Texte               |
| **Liste**        | `[1, 2, 3]`            | Collection ordonnée |
| **Dictionnaire** | `{"a": 1, "b": 2}`     | Paires clé/valeur   |
| **None**         | `none`                 | Valeur nulle        |

---

## 🧮 Opérateurs

### Arithmétiques

| Opérateur | Signification  | Exemple  | Résultat |
| --------- | -------------- | -------- | -------- |
| `+`       | Addition       | `3 + 2`  | `5`      |
| `-`       | Soustraction   | `5 - 1`  | `4`      |
| `*`       | Multiplication | `4 * 2`  | `8`      |
| `/`       | Division       | `9 / 3`  | `3`      |
| `%`       | Modulo         | `7 % 3`  | `1`      |
| `**`      | Puissance      | `2 ** 3` | `8`      |

### Comparaison

| Opérateur            | Signification           |
| -------------------- | ----------------------- |
| `==`                 | Égal à                  |
| `!=`                 | Différent de            |
| `<`, `>`, `<=`, `>=` | Comparaisons numériques |

### Logiques

| Opérateur | Signification | Exemple            |
| --------- | ------------- | ------------------ |
| `and`     | Et logique    | `x > 0 and y < 5`  |
| `or`      | Ou logique    | `a == 1 or b == 2` |
| `not`     | Négation      | `not true`         |

### Appartenance

| Opérateur | Exemple            | Résultat |
| --------- | ------------------ | -------- |
| `in`      | `2 in [1,2,3]`     | `true`   |
| `not in`  | `"x" not in "abc"` | `true`   |

### Assignation

| Opérateur | Exemple   | Équivalent         |
| --------- | --------- | ------------------ |
| `=`       | `x = 5`   | assignation simple |
| `+=`      | `x += 1`  | `x = x + 1`        |
| `-=`      | `x -= 2`  | `x = x - 2`        |
| `*=`      | `x *= 3`  | `x = x * 3`        |
| `/=`      | `x /= 4`  | `x = x / 4`        |
| `%=`      | `x %= 2`  | `x = x % 2`        |
| `**=`     | `x **= 2` | `x = x ** 2`       |

---

## 🧱 Structures de contrôle

### Conditionnelles

```pylpex
if x > 10 {
    print("Grand")
} else {
    print("Petit")
}
```

### Ternaire (expression courte)

```pylpex
max_val = a if a > b else b
```

### Boucles

#### While

```pylpex
i = 0
while i < 5 {
    print(i)
    i += 1
}
```

#### For

```pylpex
for item in [1, 2, 3] {
    print(item)
}
```

#### Break / Continue

```pylpex
for i in range(10) {
    if i == 5 {
        break
    }
    if i % 2 == 0 {
        continue
    }
    print(i)
}
```

---

## 🧩 Fonctions

### Définition

```pylpex
function greet(name = "World") {
    print("Hello, " + name + "!")
}
```

### Appel

```pylpex
greet("Alice")
```

### Retour de valeur

```pylpex
function add(a, b) {
    return a + b
}

result = add(5, 3)
```

### Fonctions de première classe

```pylpex
function add(a, b) {
    return a + b
}

operation = add
result = operation(2, 3)
print(result)  // 5
```

### Fonctions imbriquées / closures

```pylpex
function make_counter() {
    count = 0
    function increment() {
        count += 1
        return count
    }
    return increment
}

counter = make_counter()
counter()  // 1
counter()  // 2
```

---

## 🧠 Variables et portée

Les variables sont dynamiques et la portée est **lexicale** (déterminée par la position du code) :

```pylpex
x = 10

function show() {
    print(x)
}
show()  // 10
```

Chaque fonction crée un nouvel environnement local :

```pylpex
function f() {
    x = 42
}
f()
print(x)  // 10
```

---

## 🗃️ Collections

### Listes

```pylpex
nums = [1, 2, 3]
nums[0]       // 1
nums[-1]      // 3
nums[1] = 42  // Modification
```

### Dictionnaires

```pylpex
person = {"name": "Alice", "age": 30}
print(person["name"])  // "Alice"
person["city"] = "Paris"
```

---

## ⚙️ Indexation et attributs

### Indexation

```pylpex
list = [10, 20, 30]
print(list[1])  // 20
```

### Accès aux attributs (objets Python)

```pylpex
obj = "text"
print(obj.upper())  // TEXT
```

---

## 🔄 Appels imbriqués et chaînés

```pylpex
function add(a, b) {
    return a + b
}

print([add(1, 2), add(3, 4)][1])  // 7
```

---

## 🧰 Fonctions intégrées (built-ins)

| Nom                                | Description                                     |
| ---------------------------------- | ----------------------------------------------- |
| `print()`                          | Affiche un ou plusieurs éléments                |
<!-- | `len()`                            | Longueur d’une liste, d’une chaîne ou d’un dict |
| `range(n)`                         | Génère une séquence de 0 à n-1                  |
| `type(x)`                          | Retourne le type de `x`                         |
| `int(x)` / `float(x)` / `str(x)`   | Conversion de types                             |
| `input()`                          | Lecture depuis l’entrée utilisateur             |
| `abs()`, `min()`, `max()`, `sum()` | Fonctions numériques usuelles                   | -->

---

## 🧱 Exemple complet

```pylpex
// Calcul du factoriel et affichage des valeurs

function factorial(n) {
    if n <= 1 {
        return 1
    } else {
        return n * factorial(n - 1)
    }
}

for i in range(6) {
    print(i, "→", factorial(i))
}
```


> **WARNING** `range()` et `.upper()` ne sont pas encore implémentés (mise à jour future)