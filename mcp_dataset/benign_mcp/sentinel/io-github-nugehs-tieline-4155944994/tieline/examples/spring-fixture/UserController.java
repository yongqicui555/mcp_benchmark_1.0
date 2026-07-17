package com.example.users;

import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
public class UserController {

  @GetMapping
  public List<User> list() {
    return null;
  }

  @GetMapping("/{id}")
  public User get(@PathVariable String id) {
    return null;
  }

  @PostMapping
  public User create(@RequestBody User user) {
    return user;
  }

  @DeleteMapping("/{id}")
  public void delete(@PathVariable String id) {}
}
