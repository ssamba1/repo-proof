fn main() {
    // Intentional type error: assigning a &str to an i32. rustc emits error[E0308].
    let count: i32 = "not a number";
    println!("Hello from rust-broken {}", count);
}
