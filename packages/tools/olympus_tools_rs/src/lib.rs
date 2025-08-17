use pyo3::prelude::*;
use pyo3::types::{PyDict, PyBytes};
use cap_std::fs::Dir;
use std::io::{Read, Write};

#[pyfunction]
fn list_dir(py: Python, path: String) -> PyResult<PyObject> {
    let dir = Dir::open_ambient_dir(path, cap_std::ambient_authority())?;
    let mut entries = vec![];
    for entry in dir.entries()? {
        let entry = entry?;
        let metadata = entry.metadata()?;
        let entry_dict = PyDict::new(py);
        entry_dict.set_item("name", entry.file_name())?;
        entry_dict.set_item("is_dir", metadata.is_dir())?;
        entry_dict.set_item("size", metadata.len())?;
        entries.push(entry_dict.to_object(py));
    }
    Ok(entries.to_object(py))
}

#[pyfunction]
fn read_file(py: Python, path: String) -> PyResult<PyObject> {
    let mut file = std::fs::File::open(path)?;
    let mut data = Vec::new();
    file.read_to_end(&mut data)?;
    Ok(PyBytes::new(py, &data).to_object(py))
}

#[pyfunction]
fn write_file(path: String, content: &PyBytes) -> PyResult<()> {
    let mut file = std::fs::File::create(path)?;
    file.write_all(content.as_bytes())?;
    Ok(())
}

#[pyfunction]
fn delete_path(path: String, recursive: bool) -> PyResult<()> {
    if std::fs::metadata(&path)?.is_dir() {
        if recursive {
            std::fs::remove_dir_all(path)?;
        } else {
            std::fs::remove_dir(path)?;
        }
    } else {
        std::fs::remove_file(path)?;
    }
    Ok(())
}

#[pymodule]
fn olympus_tools_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(list_dir, m)?)?;
    m.add_function(wrap_pyfunction!(read_file, m)?)?;
    m.add_function(wrap_pyfunction!(write_file, m)?)?;
    m.add_function(wrap_pyfunction!(delete_path, m)?)?;
    Ok(())
}