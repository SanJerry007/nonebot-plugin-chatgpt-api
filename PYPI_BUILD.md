# Build PyPI Package

> 务必先移除 LICENSE 文件，否则会影响 build 结果，导致上传出错

安装环境

```bash
pip install --upgrade setuptools wheel build twine
```

移除旧的 build 文件

```bash
rm -rf dist *.egg-info
```

编译新的 build 文件

```bash
python -m build
```

上传到 PyPI

```bash
twine upload dist/*
```

## 自动设置 PyPI API Token

在用户根目录创建 `.pypirc` 文件，添加以下内容

```ini
[pypi]
username = __token__
password = pypi令牌
```