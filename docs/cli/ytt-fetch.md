# ytt-fetch

(Y)ou(T)ube (T)ranscript-(Fetch)ing Utility.

## Usage

```bash
ytt-fetch [OPTIONS] URL
```

## Options

```
-l, --lang TEXT     Language code for transcript (default: en)
-o, --output PATH   Save transcript text to file
```

## Examples

### Download English Transcript
```bash
ytt-fetch "https://youtube.com/watch?v=example" -l en -o transcript.txt
```

### Print Transcript to Console
```bash
ytt-fetch "https://youtube.com/watch?v=example"
```