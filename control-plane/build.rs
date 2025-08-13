fn main() {
    tonic_build::configure()
        .compile(&["../proto/cognitive/v1/task.proto"], &["../proto"])
        .unwrap();
    println!("cargo:rerun-if-changed=../proto/cognitive/v1/task.proto");
}
